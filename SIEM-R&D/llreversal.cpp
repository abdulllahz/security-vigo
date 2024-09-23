class node{
    void* data;
    node* next;
}

class head{
    node* point;    
}


head* reverse(head* target){
        node* N=target->point;
        node* NMinus1=NULL;
        node* T0=NULL;
        while(N->next!=NULL){
            T0=N;
            N=N->next;
            T0->next=NMinus1;
            NMinus1=T0;
        }
        N.next = NMinus1;
        point = N;
        head = T0
        return head;
}
========================
K-1      K  ->  K+1
^N-1     ^N
         ^T0se logs from several applications and third-party security tools, including VirusTotal, Windows Defender, ClamAV, and mor
                ^N
K-1  <-  K      K+1
         ^N-1   ^N
========================
NULL     K  ->  K+1
^N-1     ^N
         ^T0
                ^N
K-1  <-  K      K+1
         ^N-1   ^N
========================
K-1      K  ->  NULL
^N-1     ^N
         ^T0
K-1  <-  K      NULL
