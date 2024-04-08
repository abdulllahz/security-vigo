/*rule Generic_Secrets {
    strings:
        $md5 = /[a-fA-F0-9]{32}/
        $sha1 = /[a-fA-F0-9]{40}/
        $sha224 = /[a-fA-F0-9]{56}/
        $sha256 = /[a-fA-F0-9]{64}/
        $sha384 = /[a-fA-F0-9]{96}/
        $sha512 = /[a-fA-F0-9]{128}/
        $bcrypt2 = /\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}/
        $privatekey = "-----BEGIN RSA PRIVATE KEY-----"
        $publickey = "-----BEGIN PUBLIC KEY-----"
        $signatureRSA = /([A-Za-z0-9\-_]){342}/
    condition:
        $md5 or $sha1 or $sha224 or $sha256 or $sha384 or $sha512 or $bcrypt2 or $privatekey or $publickey or $signatureRSA
}*/