#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <ctype.h>
#include <unistd.h>
#include <stdint.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/un.h>

// ==================== Chunked linked list (fixed 8KB buffer per node) ====================
#define NODE_BUF_SIZE 8192

typedef struct Node {
    char data[NODE_BUF_SIZE];
    struct Node *next;
} Node;

void list_append(Node **head, const char *content) {
    Node *new_node = malloc(sizeof(Node));
    if (!new_node) {
        char errbuf[256];
        snprintf(errbuf, sizeof(errbuf), "malloc: %s\n", strerror(errno));
        write(STDERR_FILENO, errbuf, strlen(errbuf));
        exit(1);
    }
    snprintf(new_node->data, NODE_BUF_SIZE, "%s", content);
    new_node->next = NULL;
    if (*head == NULL) { *head = new_node; return; }
    Node *cur = *head;
    while (cur->next != NULL) cur = cur->next;
    cur->next = new_node;
}

void list_free_all(Node **head) {
    Node *cur = *head;
    while (cur != NULL) {
        Node *next = cur->next;
        free(cur);
        cur = next;
    }
    *head = NULL;
}

// ==================== Writer: builds one process's JSON, chunking across nodes ====================
typedef struct {
    Node **head;
    char buf[NODE_BUF_SIZE];
    size_t used;
} Writer;

void writer_init(Writer *w, Node **head) {
    w->head = head;
    w->used = 0;
    w->buf[0] = '\0';
}

void writer_flush(Writer *w) {
    if (w->used == 0) return;
    list_append(w->head, w->buf);
    w->used = 0;
    w->buf[0] = '\0';
}

void writer_append_raw(Writer *w, const char *s, size_t len) {
    if (w->used + len >= NODE_BUF_SIZE) {
        writer_flush(w);
        if (len >= NODE_BUF_SIZE) len = NODE_BUF_SIZE - 1;
    }
    memcpy(w->buf + w->used, s, len);
    w->used += len;
    w->buf[w->used] = '\0';
}

#define APPEND(...) do { \
    char _line[1024]; \
    int _n = snprintf(_line, sizeof(_line), __VA_ARGS__); \
    if (_n > 0) writer_append_raw(w, _line, (size_t)_n < sizeof(_line) ? (size_t)_n : sizeof(_line) - 1); \
} while (0)

// ==================== JSON helpers ====================
void json_esc(Writer *w, const char *s) {
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        switch (*p) {
            case '"':  writer_append_raw(w, "\\\"", 2); break;
            case '\\': writer_append_raw(w, "\\\\", 2); break;
            case '\n': writer_append_raw(w, "\\n", 2); break;
            case '\r': writer_append_raw(w, "\\r", 2); break;
            case '\t': writer_append_raw(w, "\\t", 2); break;
            default:
                if (*p < 0x20) {
                    char buf[8];
                    int n = snprintf(buf, sizeof(buf), "\\u%04x", *p);
                    writer_append_raw(w, buf, (size_t)n);
                } else {
                    char c = (char)*p;
                    writer_append_raw(w, &c, 1);
                }
        }
    }
}

void json_comma(Writer *w, int *first) {
    if (!*first) APPEND(",");
    *first = 0;
}

void json_key_str(Writer *w, int *first, const char *key, const char *val) {
    json_comma(w, first);
    APPEND("\"%s\":\"", key);
    json_esc(w, val);
    APPEND("\"");
}

void json_key_char(Writer *w, int *first, const char *key, char val) {
    char s[2] = { val, '\0' };
    json_key_str(w, first, key, s);
}

void json_key_long(Writer *w, int *first, const char *key, long val) {
    json_comma(w, first);
    APPEND("\"%s\":%ld", key, val);
}

void json_key_ulong(Writer *w, int *first, const char *key, unsigned long val) {
    json_comma(w, first);
    APPEND("\"%s\":%lu", key, val);
}

void json_key_long_or_null(Writer *w, int *first, const char *key, long val, int available) {
    json_comma(w, first);
    if (available) APPEND("\"%s\":%ld", key, val);
    else APPEND("\"%s\":null", key);
}

void json_array_start(Writer *w, int *obj_first, const char *key) {
    json_comma(w, obj_first);
    APPEND("\"%s\":[", key);
}

void json_array_end(Writer *w) {
    APPEND("]");
}

static void proc_path(int pid, const char *suffix, char *out, size_t out_size) {
    snprintf(out, out_size, "/proc/%d/%s", pid, suffix);
}

typedef struct {
    int pid;
    char comm[256];
    char state;
    long ppid;
    long pgrp;
    long session;
    long tty_nr;
    long utime;
    long stime;
    long num_threads;
    long priority;
    long nice;
    unsigned long vsize;
    long starttime;
    long processor;
    long rt_priority;
    long policy;
} proc_stat_t;

typedef struct {
    long vmpeak_kb, vmsize_kb, vmhwm_kb, vmrss_kb;
    long vmdata_kb, vmstk_kb, vmexe_kb, vmlib_kb, vmswap_kb;
    long voluntary_ctxt, nonvoluntary_ctxt;
    long uid, gid;
} proc_status_t;

typedef struct {
    long rchar, wchar, syscr, syscw, read_bytes, write_bytes;
} proc_io_t;

typedef struct {
    unsigned long size_pages, resident_pages, shared_pages;
    unsigned long text_pages, lib_pages, data_pages;
} proc_statm_t;

int read_proc_stat(int pid, proc_stat_t *ps) {
    char path[64];
    proc_path(pid, "stat", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f) return -1;

    char comm_raw[300];
    long unused_l; unsigned long unused_lu; unsigned unused_u;

    int n = fscanf(f,
        "%d (%299[^)]) %c %ld %ld %ld %ld %*d %u "
        "%lu %lu %lu %lu "
        "%ld %ld %ld %ld "
        "%ld %ld %ld %ld "
        "%ld %lu "
        "%*u %*u %*u %*u %*u %*u %*u %*u %*u %*u "
        "%*u %*u %*u %*u %*u "
        "%ld %ld %ld ",
        &ps->pid, comm_raw, &ps->state, &ps->ppid, &ps->pgrp, &ps->session, &ps->tty_nr,
        &unused_u,
        &unused_lu, &unused_lu, &unused_lu, &unused_lu,
        &ps->utime, &ps->stime, &unused_l, &unused_l,
        &ps->priority, &ps->nice, &ps->num_threads, &unused_l,
        &ps->starttime, &ps->vsize,
        &ps->processor, &ps->rt_priority, &ps->policy);

    fclose(f);
    if (n < 25) return -1;

    strncpy(ps->comm, comm_raw, sizeof(ps->comm) - 1);
    ps->comm[sizeof(ps->comm) - 1] = '\0';
    return 0;
}

int read_proc_status(int pid, proc_status_t *pst) {
    char path[64];
    proc_path(pid, "status", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f) return -1;

    pst->vmpeak_kb = pst->vmsize_kb = pst->vmhwm_kb = pst->vmrss_kb = -1;
    pst->vmdata_kb = pst->vmstk_kb = pst->vmexe_kb = pst->vmlib_kb = pst->vmswap_kb = -1;
    pst->voluntary_ctxt = pst->nonvoluntary_ctxt = -1;
    pst->uid = pst->gid = -1;

    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if      (!strncmp(line, "VmPeak:", 7))  sscanf(line, "VmPeak: %ld", &pst->vmpeak_kb);
        else if (!strncmp(line, "VmSize:", 7))  sscanf(line, "VmSize: %ld", &pst->vmsize_kb);
        else if (!strncmp(line, "VmHWM:", 6))   sscanf(line, "VmHWM: %ld", &pst->vmhwm_kb);
        else if (!strncmp(line, "VmRSS:", 6))   sscanf(line, "VmRSS: %ld", &pst->vmrss_kb);
        else if (!strncmp(line, "VmData:", 7))  sscanf(line, "VmData: %ld", &pst->vmdata_kb);
        else if (!strncmp(line, "VmStk:", 6))   sscanf(line, "VmStk: %ld", &pst->vmstk_kb);
        else if (!strncmp(line, "VmExe:", 6))   sscanf(line, "VmExe: %ld", &pst->vmexe_kb);
        else if (!strncmp(line, "VmLib:", 6))   sscanf(line, "VmLib: %ld", &pst->vmlib_kb);
        else if (!strncmp(line, "VmSwap:", 7))  sscanf(line, "VmSwap: %ld", &pst->vmswap_kb);
        else if (!strncmp(line, "voluntary_ctxt_switches:", 24))
            sscanf(line, "voluntary_ctxt_switches: %ld", &pst->voluntary_ctxt);
        else if (!strncmp(line, "nonvoluntary_ctxt_switches:", 27))
            sscanf(line, "nonvoluntary_ctxt_switches: %ld", &pst->nonvoluntary_ctxt);
        else if (!strncmp(line, "Uid:", 4)) sscanf(line, "Uid: %ld", &pst->uid);
        else if (!strncmp(line, "Gid:", 4)) sscanf(line, "Gid: %ld", &pst->gid);
    }
    fclose(f);
    return 0;
}

int read_proc_statm(int pid, proc_statm_t *sm) {
    char path[64];
    proc_path(pid, "statm", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    int n = fscanf(f, "%lu %lu %lu %lu %lu %lu",
        &sm->size_pages, &sm->resident_pages, &sm->shared_pages,
        &sm->text_pages, &sm->lib_pages, &sm->data_pages);
    fclose(f);
    return (n == 6) ? 0 : -1;
}

int read_proc_io(int pid, proc_io_t *io) {
    char path[64];
    proc_path(pid, "io", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f) return -1;

    io->rchar = io->wchar = io->syscr = io->syscw = io->read_bytes = io->write_bytes = -1;

    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if      (!strncmp(line, "rchar:", 6))        sscanf(line, "rchar: %ld", &io->rchar);
        else if (!strncmp(line, "wchar:", 6))        sscanf(line, "wchar: %ld", &io->wchar);
        else if (!strncmp(line, "syscr:", 6))        sscanf(line, "syscr: %ld", &io->syscr);
        else if (!strncmp(line, "syscw:", 6))        sscanf(line, "syscw: %ld", &io->syscw);
        else if (!strncmp(line, "read_bytes:", 11))  sscanf(line, "read_bytes: %ld", &io->read_bytes);
        else if (!strncmp(line, "write_bytes:", 12)) sscanf(line, "write_bytes: %ld", &io->write_bytes);
    }
    fclose(f);
    return 0;
}

long read_oom_score(int pid) {
    char path[64];
    proc_path(pid, "oom_score", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    long score = -1;
    fscanf(f, "%ld", &score);
    fclose(f);
    return score;
}

void read_cmdline(int pid, char *out, size_t out_size) {
    char path[64];
    proc_path(pid, "cmdline", path, sizeof(path));
    FILE *f = fopen(path, "r");
    out[0] = '\0';
    if (!f) return;
    size_t n = fread(out, 1, out_size - 1, f);
    fclose(f);
    for (size_t i = 0; i < n; i++)
        if (out[i] == '\0') out[i] = ' ';
    out[n] = '\0';
}

void read_link_target(const char *procfile, int pid, char *out, size_t out_size) {
    char path[64];
    proc_path(pid, procfile, path, sizeof(path));
    ssize_t n = readlink(path, out, out_size - 1);
    out[n > 0 ? n : 0] = '\0';
    if (n < 0) strcpy(out, "unavailable");
}

int count_open_fds(int pid) {
    char path[64];
    proc_path(pid, "fd", path, sizeof(path));
    DIR *d = opendir(path);
    if (!d) return -1;
    int count = 0;
    struct dirent *entry;
    while ((entry = readdir(d)) != NULL) {
        if (entry->d_name[0] == '.') continue;
        count++;
    }
    closedir(d);
    return count;
}

const char *tcp_state_name(unsigned int state) {
    switch (state) {
        case 0x01: return "ESTABLISHED";
        case 0x02: return "SYN_SENT";
        case 0x03: return "SYN_RECV";
        case 0x04: return "FIN_WAIT1";
        case 0x05: return "FIN_WAIT2";
        case 0x06: return "TIME_WAIT";
        case 0x07: return "CLOSE";
        case 0x08: return "CLOSE_WAIT";
        case 0x09: return "LAST_ACK";
        case 0x0A: return "LISTEN";
        case 0x0B: return "CLOSING";
        default:   return "UNKNOWN";
    }
}

void decode_tcp_addr(const char *hex_field, char *out, size_t out_size) {
    unsigned int b0, b1, b2, b3, port;
    sscanf(hex_field, "%2x%2x%2x%2x:%4x", &b3, &b2, &b1, &b0, &port);
    snprintf(out, out_size, "%u.%u.%u.%u:%u", b0, b1, b2, b3, port);
}

void json_openfdlist(int pid, Writer *w, int *obj_first) {
    json_array_start(w, obj_first, "OpenFDlist");
    int arr_first = 1;

    char path[64];
    proc_path(pid, "fd", path, sizeof(path));
    DIR *d = opendir(path);
    if (d) {
        struct dirent *entry;
        while ((entry = readdir(d)) != NULL) {
            if (entry->d_name[0] == '.') continue;

            char fd_path[320], target[256];
            snprintf(fd_path, sizeof(fd_path), "%s/%s", path, entry->d_name);
            ssize_t n = readlink(fd_path, target, sizeof(target) - 1);
            target[n > 0 ? n : 0] = '\0';
            if (n < 0) strcpy(target, "unreadable");

            json_comma(w, &arr_first);
            APPEND("{\"FD %s\":\"", entry->d_name);
            json_esc(w, target);
            APPEND("\"}");
        }
        closedir(d);
    }
    json_array_end(w);
}

void json_memorymap(int pid, Writer *w, int *obj_first) {
    json_array_start(w, obj_first, "MemoryMap");
    int arr_first = 1;

    char path[64];
    proc_path(pid, "maps", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (f) {
        char line[512];
        while (fgets(line, sizeof(line), f)) {
            line[strcspn(line, "\n")] = 0;

            char addr_range[64], perms[8], pathname[256];
            pathname[0] = '\0';
            sscanf(line, "%63s %7s %*s %*s %*s %255[^\n]", addr_range, perms, pathname);

            char *p = pathname;
            while (isspace((unsigned char)*p)) p++;

            char start_hex[32] = "", end_hex[32] = "";
            char *dash = strchr(addr_range, '-');
            if (dash) {
                size_t start_len = (size_t)(dash - addr_range);
                if (start_len >= sizeof(start_hex)) start_len = sizeof(start_hex) - 1;
                memcpy(start_hex, addr_range, start_len);
                start_hex[start_len] = '\0';
                snprintf(end_hex, sizeof(end_hex), "%s", dash + 1);
            }

            json_comma(w, &arr_first);
            APPEND("{\"start\":0x%s,\"end\":0x%s,\"flag\":\"", start_hex, end_hex);
            json_esc(w, perms);
            APPEND("\",\"content\":\"");
            json_esc(w, p[0] ? p : "[anonymous]");
            APPEND("\"}");
        }
        fclose(f);
    }
    json_array_end(w);
}

void json_network(int pid, Writer *w, int *obj_first) {
    json_array_start(w, obj_first, "Network");
    int arr_first = 1;
    char path[64];

    proc_path(pid, "net/tcp", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (f) {
        char line[512];
        int first_line = 1;
        while (fgets(line, sizeof(line), f)) {
            if (first_line) { first_line = 0; continue; }
            char local_hex[32], rem_hex[32];
            unsigned int state;
            unsigned long tx_queue, rx_queue, uid_val, inode;
            int n = sscanf(line, "%*d: %31s %31s %x %lx:%lx %*x:%*x %*x %lu %*d %lu",
                local_hex, rem_hex, &state, &tx_queue, &rx_queue, &uid_val, &inode);
            if (n < 7) continue;
            char local_str[32], rem_str[32];
            decode_tcp_addr(local_hex, local_str, sizeof(local_str));
            decode_tcp_addr(rem_hex, rem_str, sizeof(rem_str));

            json_comma(w, &arr_first);
            APPEND("{\"proto\":\"TCP\",\"localaddr\":\"%s\",\"remoteaddr\":\"%s\",\"mode\":\"%s\",\"txq\":%lu,\"rxq\":%lu,\"uid\":%lu,\"inode\":%lu}",
                local_str, rem_str, tcp_state_name(state), tx_queue, rx_queue, uid_val, inode);
        }
        fclose(f);
    }

    proc_path(pid, "net/udp", path, sizeof(path));
    f = fopen(path, "r");
    if (f) {
        char line[512];
        int first_line = 1;
        while (fgets(line, sizeof(line), f)) {
            if (first_line) { first_line = 0; continue; }
            char local_hex[32], rem_hex[32];
            unsigned long tx_queue, rx_queue, uid_val, inode;
            int n = sscanf(line, "%*d: %31s %31s %*x %lx:%lx %*x:%*x %*x %lu %*d %lu",
                local_hex, rem_hex, &tx_queue, &rx_queue, &uid_val, &inode);
            if (n < 6) continue;
            char local_str[32], rem_str[32];
            decode_tcp_addr(local_hex, local_str, sizeof(local_str));
            decode_tcp_addr(rem_hex, rem_str, sizeof(rem_str));

            json_comma(w, &arr_first);
            APPEND("{\"proto\":\"UDP\",\"localaddr\":\"%s\",\"remoteaddr\":\"%s\",\"mode\":\"\",\"txq\":%lu,\"rxq\":%lu,\"uid\":%lu,\"inode\":%lu}",
                local_str, rem_str, tx_queue, rx_queue, uid_val, inode);
        }
        fclose(f);
    }

    proc_path(pid, "net/sockstat", path, sizeof(path));
    f = fopen(path, "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            line[strcspn(line, "\n")] = 0;
            if (strncmp(line, "sockets:", 8) != 0 &&
                strncmp(line, "TCP:", 4) != 0 &&
                strncmp(line, "UDP:", 4) != 0) continue;

            char label[16];
            sscanf(line, "%15[^:]", label);

            char copy[256];
            strncpy(copy, line, sizeof(copy) - 1); copy[sizeof(copy) - 1] = 0;
            char *save;
            char *tok = strtok_r(copy, " \t", &save);
            tok = strtok_r(NULL, " \t", &save);
            while (tok) {
                char *key = tok;
                char *val = strtok_r(NULL, " \t", &save);
                if (!val) break;

                json_comma(w, &arr_first);
                APPEND("{\"proto\":\"SOCKSTAT\",\"metric\":\"%s.%s\",\"value\":%s}", label, key, val);

                tok = strtok_r(NULL, " \t", &save);
            }
        }
        fclose(f);
    }

    proc_path(pid, "net/snmp", path, sizeof(path));
    f = fopen(path, "r");
    if (f) {
        const char *tcp_fields[] = {"ActiveOpens", "PassiveOpens", "AttemptFails",
                                     "EstabResets", "CurrEstab", "InSegs", "OutSegs",
                                     "RetransSegs", "InErrs", "OutRsts", NULL};
        const char *udp_fields[] = {"InDatagrams", "OutDatagrams", "NoPorts", "InErrors", NULL};

        char header_line[1024], value_line[1024];
        while (fgets(header_line, sizeof(header_line), f)) {
            if (!fgets(value_line, sizeof(value_line), f)) break;
            char label[16];
            sscanf(header_line, "%15[^:]", label);
            const char **wanted = NULL;
            if (strcmp(label, "Tcp") == 0) wanted = tcp_fields;
            else if (strcmp(label, "Udp") == 0) wanted = udp_fields;
            if (!wanted) continue;

            char h_copy[1024], v_copy[1024];
            strncpy(h_copy, header_line, sizeof(h_copy) - 1); h_copy[sizeof(h_copy)-1] = 0;
            strncpy(v_copy, value_line, sizeof(v_copy) - 1); v_copy[sizeof(v_copy)-1] = 0;

            char *h_save, *v_save;
            char *h_tok = strtok_r(h_copy, " \t\n", &h_save);
            char *v_tok = strtok_r(v_copy, " \t\n", &v_save);
            h_tok = strtok_r(NULL, " \t\n", &h_save);
            v_tok = strtok_r(NULL, " \t\n", &v_save);

            while (h_tok && v_tok) {
                for (int i = 0; wanted[i]; i++) {
                    if (strcmp(h_tok, wanted[i]) == 0) {
                        json_comma(w, &arr_first);
                        APPEND("{\"proto\":\"SNMP\",\"metric\":\"%s.%s\",\"value\":%s}", label, h_tok, v_tok);
                        break;
                    }
                }
                h_tok = strtok_r(NULL, " \t\n", &h_save);
                v_tok = strtok_r(NULL, " \t\n", &v_save);
            }
        }
        fclose(f);
    }

    json_array_end(w);
}

void json_nic(int pid, Writer *w, int *obj_first) {
    json_array_start(w, obj_first, "Nic");
    int arr_first = 1;

    char path[64];
    proc_path(pid, "net/dev", path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (f) {
        char line[512];
        int line_num = 0;
        while (fgets(line, sizeof(line), f)) {
            line_num++;
            if (line_num <= 2) continue;

            char iface[64];
            unsigned long rx_bytes, rx_packets, rx_errs, rx_drop;
            unsigned long tx_bytes, tx_packets, tx_errs, tx_drop;

            char *colon = strchr(line, ':');
            if (!colon) continue;
            *colon = '\0';
            char *name_start = line;
            while (isspace((unsigned char)*name_start)) name_start++;
            strncpy(iface, name_start, sizeof(iface) - 1);
            iface[sizeof(iface) - 1] = '\0';

            int n = sscanf(colon + 1,
                "%lu %lu %lu %lu %*u %*u %*u %*u %lu %lu %lu %lu",
                &rx_bytes, &rx_packets, &rx_errs, &rx_drop,
                &tx_bytes, &tx_packets, &tx_errs, &tx_drop);
            if (n < 8) continue;

            json_comma(w, &arr_first);
            APPEND("{\"iface\":\"");
            json_esc(w, iface);
            APPEND("\",\"rxbytes\":%lu,\"rxpckt\":%lu,\"rxerr\":%lu,\"rxdrp\":%lu,"
                   "\"txbytes\":%lu,\"txpckt\":%lu,\"txerr\":%lu,\"txdrp\":%lu}",
                rx_bytes, rx_packets, rx_errs, rx_drop,
                tx_bytes, tx_packets, tx_errs, tx_drop);
        }
        fclose(f);
    }
    json_array_end(w);
}

void build_process_json(int pid, Writer *w) {
    proc_stat_t ps;
    if (read_proc_stat(pid, &ps) != 0) return;

    proc_status_t pst;   read_proc_status(pid, &pst);
    proc_statm_t sm;     int has_statm = (read_proc_statm(pid, &sm) == 0);
    proc_io_t io;        int has_io    = (read_proc_io(pid, &io) == 0);
    long oom_score        = read_oom_score(pid);
    int fd_count           = count_open_fds(pid);

    char cmdline[512]; read_cmdline(pid, cmdline, sizeof(cmdline));
    char exe_path[256]; read_link_target("exe", pid, exe_path, sizeof(exe_path));
    char cwd_path[256]; read_link_target("cwd", pid, cwd_path, sizeof(cwd_path));

    int first = 1;
    APPEND("{");

    json_key_long(w, &first, "PID", ps.pid);
    json_key_str(w, &first, "Name", ps.comm);
    json_key_str(w, &first, "Cmdline", cmdline[0] ? cmdline : "(kernel thread / unavailable)");
    json_key_str(w, &first, "Exepath", exe_path);
    json_key_str(w, &first, "Cwd", cwd_path);
    json_key_char(w, &first, "State", ps.state);
    json_key_long(w, &first, "PPID", ps.ppid);
    json_key_long(w, &first, "PGID", ps.pgrp);
    json_key_long(w, &first, "SID", ps.session);
    json_key_long(w, &first, "TTY", ps.tty_nr);
    json_key_long(w, &first, "Threads", ps.num_threads);
    json_key_long(w, &first, "Priority", ps.priority);
    json_key_long(w, &first, "Nice", ps.nice);
    json_key_long(w, &first, "RTpriority", ps.rt_priority);
    json_key_long(w, &first, "Schedpolicy", ps.policy);
    json_key_long(w, &first, "LastCPUcore", ps.processor);
    json_key_long(w, &first, "Starttime", ps.starttime);
    json_key_long(w, &first, "UserCPU", ps.utime);
    json_key_long(w, &first, "SystemCPU", ps.stime);
    json_key_ulong(w, &first, "Virtualmem", ps.vsize);

    json_key_long_or_null(w, &first, "UID", pst.uid, pst.uid >= 0);
    json_key_long_or_null(w, &first, "GID", pst.gid, pst.gid >= 0);
    json_key_long_or_null(w, &first, "VmPeak", pst.vmpeak_kb, pst.vmpeak_kb >= 0);
    json_key_long_or_null(w, &first, "VmSize", pst.vmsize_kb, pst.vmsize_kb >= 0);
    json_key_long_or_null(w, &first, "VmHWM", pst.vmhwm_kb, pst.vmhwm_kb >= 0);
    json_key_long_or_null(w, &first, "VmRSS", pst.vmrss_kb, pst.vmrss_kb >= 0);
    json_key_long_or_null(w, &first, "VmData", pst.vmdata_kb, pst.vmdata_kb >= 0);
    json_key_long_or_null(w, &first, "VmStk", pst.vmstk_kb, pst.vmstk_kb >= 0);
    json_key_long_or_null(w, &first, "VmExe", pst.vmexe_kb, pst.vmexe_kb >= 0);
    json_key_long_or_null(w, &first, "VmLib", pst.vmlib_kb, pst.vmlib_kb >= 0);
    json_key_long_or_null(w, &first, "VmSwap", pst.vmswap_kb, pst.vmswap_kb >= 0);
    json_key_long_or_null(w, &first, "Voluntaryswitches", pst.voluntary_ctxt, pst.voluntary_ctxt >= 0);
    json_key_long_or_null(w, &first, "Involuntaryswitches", pst.nonvoluntary_ctxt, pst.nonvoluntary_ctxt >= 0);

    json_key_long_or_null(w, &first, "statmsize", (long)sm.size_pages, has_statm);
    json_key_long_or_null(w, &first, "statmresident", (long)sm.resident_pages, has_statm);
    json_key_long_or_null(w, &first, "statmshared", (long)sm.shared_pages, has_statm);
    json_key_long_or_null(w, &first, "statmtext", (long)sm.text_pages, has_statm);
    json_key_long_or_null(w, &first, "statmlib", (long)sm.lib_pages, has_statm);
    json_key_long_or_null(w, &first, "statmdata", (long)sm.data_pages, has_statm);

    json_key_long_or_null(w, &first, "Bytesread(cacheincl.)", io.rchar, has_io);
    json_key_long_or_null(w, &first, "Byteswritten(cacheincl.)", io.wchar, has_io);
    json_key_long_or_null(w, &first, "Bytesread(disk)", io.read_bytes, has_io);
    json_key_long_or_null(w, &first, "Byteswritten(disk)", io.write_bytes, has_io);
    json_key_long_or_null(w, &first, "Readsyscalls", io.syscr, has_io);
    json_key_long_or_null(w, &first, "Writesyscalls", io.syscw, has_io);

    json_key_long_or_null(w, &first, "OOMscore", oom_score, oom_score >= 0);
    json_key_long_or_null(w, &first, "OpenFDs", fd_count, fd_count >= 0);

    json_openfdlist(pid, w, &first);
    json_memorymap(pid, w, &first);
    json_network(pid, w, &first);
    json_nic(pid, w, &first);

    APPEND("}\n");
}

// ==================== Unix domain socket output ====================
// Local-machine-only IPC via a filesystem path instead of an IP:port.
// A separate listener process must bind() this same path before running
// this program, or every send below will fail (no listener = nobody to
// deliver to, same as UDP having no listener on a port).
#define SOCKET_PATH "/tmp/processes.sock"

int unix_socket_setup(struct sockaddr_un *dest_addr) {
    int sockfd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        char errbuf[256];
        snprintf(errbuf, sizeof(errbuf), "socket: %s\n", strerror(errno));
        write(STDERR_FILENO, errbuf, strlen(errbuf));
        return -1;
    }
    memset(dest_addr, 0, sizeof(*dest_addr));
    dest_addr->sun_family = AF_UNIX;
    strncpy(dest_addr->sun_path, SOCKET_PATH, sizeof(dest_addr->sun_path) - 1);
    return sockfd;
}

int unix_send_report(int sockfd, struct sockaddr_un *dest_addr, const char *data) {
    size_t len = strlen(data);
    ssize_t sent = sendto(sockfd, data, len, 0,
                           (struct sockaddr *)dest_addr, sizeof(*dest_addr));
    if (sent < 0) {
        char errbuf[256];
        snprintf(errbuf, sizeof(errbuf), "sendto: %s\n", strerror(errno));
        write(STDERR_FILENO, errbuf, strlen(errbuf));
        return 0;
    }
    return 1;
}

int main(void) {
    Node *report_list = NULL;

    DIR *proc_dir = opendir("/proc");
    if (!proc_dir) {
        char errbuf[256];
        snprintf(errbuf, sizeof(errbuf), "opendir /proc: %s\n", strerror(errno));
        write(STDERR_FILENO, errbuf, strlen(errbuf));
        return 1;
    }

    struct dirent *entry;
    while ((entry = readdir(proc_dir)) != NULL) {
        if (!isdigit((unsigned char)entry->d_name[0])) continue;
        int pid = atoi(entry->d_name);

        Writer w;
        writer_init(&w, &report_list);

        build_process_json(pid, &w);
        writer_flush(&w);
    }
    closedir(proc_dir);

    struct sockaddr_un unix_dest;
    int unix_fd = unix_socket_setup(&unix_dest);

    for (Node *cur = report_list; cur != NULL; cur = cur->next) {
        if (unix_fd >= 0) unix_send_report(unix_fd, &unix_dest, cur->data);
    }
    char* end="<end>\0";
    if (unix_fd >= 0) unix_send_report(unix_fd, &unix_dest, end);

    if (unix_fd >= 0) close(unix_fd);

    list_free_all(&report_list);
    return 0;
}
