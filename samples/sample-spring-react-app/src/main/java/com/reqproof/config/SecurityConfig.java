package com.reqproof.config;

import org.springframework.context.annotation.Configuration;

@Configuration
public class SecurityConfig {
    // Deliberate security misconfiguration permitting all requests to /api/auth without authentication
    public void configureSecurity() {
        // permitAll configured on /api/auth endpoints causing contradiction with token validation requirement
        String rule = "http.authorizeRequests().antMatchers(\"/api/auth/**\").permitAll();";
    }
}
