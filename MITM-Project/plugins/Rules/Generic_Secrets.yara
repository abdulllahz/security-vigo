rule Generic_Secrets {
    strings:
        $api = "api" nocase
        $token = "token" nocase
        $secret = "secret" nocase
        $key = "key" nocase
    condition:
        $api or $token or $secret or $key
}