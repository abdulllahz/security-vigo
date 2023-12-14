rule PII_SSN {
    strings:
        $cnic_pattern = /[0-9]{5}-[0-9]{7}-[0-9]/        
    condition:
        $cnic_pattern
}