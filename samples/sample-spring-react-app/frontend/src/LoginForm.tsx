import React, { useState } from 'react';

export const LoginForm: React.FC = () => {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // Client-side password validation
        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }
    };

    return (
        <form onSubmit={handleSubmit} className="login-form">
            <h2>User Login</h2>
            <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
            />
            {error && <span className="error-message">{error}</span>}
            <button type="submit">Sign In</button>
        </form>
    );
};
