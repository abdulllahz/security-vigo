rule PII_PhoneNumber {
    strings:
        $international_number = /\+?92[0-9]{10}/
        $local_number = /0[0-9]{10}/
    condition:
        $international_number or $local_number
}