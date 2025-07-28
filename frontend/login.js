// frontend/login.js

const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default form submission

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Basic client-side validation
        if (!email || !password) {
            alert('Please enter both email and password.');
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message); // e.g., "Logged in successfully"

                // --- Store the Token (Crucial for Authenticated Routes) ---
                localStorage.setItem('token', data.token);
                // You might also store user ID, email, role if needed frequently
                localStorage.setItem('userId', data.userId);
                localStorage.setItem('userEmail', data.email);
                localStorage.setItem('userRole', data.role);
                // --- End Store Token ---

                // --- Redirect based on Role ---
                if (data.role === 'Landlord') {
                    window.location.href = '../dashboards/landlord.html';
                } else if (data.role === 'Tenant') {
                    window.location.href = '../dashboards/tenant.html';
                } else {
                    // Fallback
                    window.location.href = 'index.html'; // Or a generic success page
                }
                // --- End Redirect ---

            } else {
                // Handle backend errors (e.g., invalid credentials)
                alert(`Login failed: ${data.message || 'Something went wrong.'}`);
                console.error('Backend error during login:', data);
            }
        } catch (error) {
            console.error('Network or Fetch Error during login:', error);
            alert('An error occurred during login. Please check your network and try again.');
        }
    });
} else {
    console.error('Login form not found!');
    alert('Critical error: Login form not found. Please check HTML.');
}