class JavaCryptoTransfer {
    void enviar(String email) throws Exception {
        MessageDigest.getInstance("MD5");
        new RestTemplate().postForEntity(
            "https://terceiro.example",
            new Payload(email),
            Void.class
        );
    }
}
