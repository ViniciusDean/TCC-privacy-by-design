class JavaSafeHashing {
    String proteger(String email) {
        String emailHash = sha256(email);
        return emailHash;
    }
}
