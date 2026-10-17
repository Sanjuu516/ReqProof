package com.reqproof.auth;

public class JwtValidator {
    public boolean validate(String token) {
        if (token == null || token.isEmpty()) {
            return false;
        }
        // Logic for checking expiration
        if (isExpired(token)) {
            return false;
        }
        return true;
    }

    private boolean isExpired(String token) {
        return token.contains("expired");
    }
}
