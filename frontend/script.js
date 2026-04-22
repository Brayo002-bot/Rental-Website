document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuIcon = document.querySelector('.mobile-menu-icon');
    const mobileNavMenu = document.querySelector('.mobile-nav-menu');
    const navLinks = document.querySelectorAll('.mobile-nav-menu a'); // Select all links within the mobile menu

    // Toggle mobile menu visibility
    mobileMenuIcon.addEventListener('click', () => {
        mobileNavMenu.classList.toggle('active');
    });

    // Close mobile menu when a link is clicked (for smooth scrolling)
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (mobileNavMenu.classList.contains('active')) {
                mobileNavMenu.classList.remove('active');
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    // ... (existing code for mobile menu on index.html) ...

    const mobileMenuIcon = document.querySelector('.mobile-menu-icon');
    const mobileNavMenu = document.querySelector('.mobile-nav-menu');
    const navLinks = document.querySelectorAll('.mobile-nav-menu a');

    if (mobileMenuIcon && mobileNavMenu) { // Check if elements exist (they won't on dashboard pages)
        mobileMenuIcon.addEventListener('click', () => {
            mobileNavMenu.classList.toggle('active');
        });

        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (mobileNavMenu.classList.contains('active')) {
                    mobileNavMenu.classList.remove('active');
                }
            });
        });
    }

    // Dashboard specific JavaScript
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const dashboardSidebar = document.querySelector('.dashboard-sidebar');
    const dashboardMainContent = document.querySelector('.dashboard-main-content');
    const sidebarNavLinks = document.querySelectorAll('.sidebar-nav a');
    const dashboardSections = document.querySelectorAll('.dashboard-section');

    if (sidebarToggle && dashboardSidebar) { // Check if dashboard elements exist
        sidebarToggle.addEventListener('click', () => {
            dashboardSidebar.classList.toggle('hidden');
            // Adjust main content margin based on sidebar visibility
            if (dashboardSidebar.classList.contains('hidden')) {
                dashboardMainContent.style.marginLeft = '0';
            } else {
                dashboardMainContent.style.marginLeft = '250px'; // Same as sidebar width
            }
        });
    }

    // Function to show/hide dashboard sections
    sidebarNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent default link behavior (page jump)

            // Remove 'active' class from all links and sections
            sidebarNavLinks.forEach(navLink => navLink.parentElement.classList.remove('active'));
            dashboardSections.forEach(section => section.classList.remove('active-section'));

            // Add 'active' class to the clicked link's parent (li)
            link.parentElement.classList.add('active');

            // Get the target section ID from the href (e.g., #overview)
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);

            // Show the target section
            if (targetSection) {
                targetSection.classList.add('active-section');
            }

            // Close sidebar on mobile after clicking a link
            if (window.innerWidth <= 768 && dashboardSidebar.classList.contains('active')) {
                 dashboardSidebar.classList.remove('active');
                 dashboardMainContent.style.marginLeft = '0';
            }
        });
    });

    // Initialize: Show the first section on load
    if (dashboardSections.length > 0) {
        dashboardSections[0].classList.add('active-section');
        sidebarNavLinks[0].parentElement.classList.add('active');
    }
});

// script.js

// Get a reference to the signup form
const signupForm = document.getElementById('signupForm');

// IMPORTANT: Ensure this entire block is wrapped in an event listener
// for the form submission.
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent the default form submission (page reload)

        // 1. Get values from form inputs using their IDs
        //    Make sure these IDs exactly match your HTML <input> element IDs
        const fullName = document.getElementById('fullName').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        // 2. Get the selected role from the radio buttons
        //    Make sure the 'name' attribute matches your HTML radio buttons
        const roleInput = document.querySelector('input[name="role"]:checked');
        const role = roleInput ? roleInput.value : ''; // Get the value, or empty string if none selected

        // 3. Client-side Validation (Important before sending to backend)
        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return; // Stop the function here
        }

        if (!role) {
            alert('Please select whether you are a Landlord or Tenant.');
            return; // Stop the function here
        }

        if (fullName === '' || email === '' || password === '') {
            alert('Full Name, Email, and Password are required.');
            return; // Stop the function here
        }

        if (password.length < 6) {
            alert('Password must be at least 6 characters long.');
            return; // Stop the function here
        }

        // 4. Send data to backend using Fetch API
        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fullName,
                    email,
                    password,
                    role
                }),
            });

            const data = await response.json(); // Parse the JSON response from the backend

            if (response.ok) { // Check if the HTTP status code is in the 200-299 range (e.g., 200 OK, 201 Created)
                alert(data.message); // Show success message from backend
                signupForm.reset(); // Clear the form fields

                // Redirect to the Django dashboard endpoints instead of static HTML.
                if (data.role === 'landlord') {
                    window.location.href = '/dashboards/landlord/';
                } else if (data.role === 'tenant') {
                    window.location.href = '/dashboards/tenant/';
                } else {
                    // Fallback if role is unexpected or missing (though it shouldn't be with current backend)
                    window.location.href = '/login/';
                }

            } else {
                // Handle errors from the backend (e.g., 400 Bad Request, 409 Conflict)
                alert(`Error: ${data.message || 'Something went wrong on the server.'}`);
                console.error('Backend error:', data); // Log the full error response for debugging
            }
                } catch (error) {
                    // This catch block handles network errors (e.g., server offline, CORS issues)
                    console.error('Network or Fetch Error:', error);
                    alert('An error occurred during signup. Please check your network connection and server status.');
                }
            });
        }

        // This is the JavaScript for the slider functionality
        document.addEventListener('DOMContentLoaded', () => {
            const sliderImages = document.querySelector('.slider-images');
            const images = document.querySelectorAll('.slider-images img');
            const prevBtn = document.querySelector('.prev-btn');
            const nextBtn = document.querySelector('.next-btn');
            const sliderDotsContainer = document.querySelector('.slider-dots');
        
            let currentIndex = 0;
            const totalImages = images.length;
        
            // --- Create Dots Dynamically ---
            function createDots() {
                for (let i = 0; i < totalImages; i++) {
                    const dot = document.createElement('span');
                    dot.classList.add('dot');
                    if (i === 0) {
                        dot.classList.add('active');
                    }
                    dot.dataset.index = i; // Store index for direct navigation
                    dot.addEventListener('click', () => {
                        goToSlide(parseInt(dot.dataset.index));
                    });
                    sliderDotsContainer.appendChild(dot);
                }
            }
        
            // --- Update Active Dot ---
            function updateDots() {
                document.querySelectorAll('.dot').forEach((dot, index) => {
                    if (index === currentIndex) {
                        dot.classList.add('active');
                    } else {
                        dot.classList.remove('active');
                    }
                });
            }
        
            // --- Go to Specific Slide ---
            function goToSlide(index) {
                currentIndex = index;
                // Handle loop: if index goes out of bounds, loop back
                if (currentIndex >= totalImages) {
                    currentIndex = 0;
                } else if (currentIndex < 0) {
                    currentIndex = totalImages - 1;
                }
        
                const offset = -currentIndex * 100; // Calculate percentage to slide
                sliderImages.style.transform = `translateX(${offset}%)`;
                updateDots();
            }
        
            // --- Event Listeners for Buttons ---
            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    goToSlide(currentIndex - 1);
                });
            }
        
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    goToSlide(currentIndex + 1);
                });
            }
        
            // --- Optional: Auto-play ---
            let autoPlayInterval;
            function startAutoPlay() {
                autoPlayInterval = setInterval(() => {
                    goToSlide(currentIndex + 1);
                }, 5000); // Change image every 5 seconds
            }
        
            function stopAutoPlay() {
                clearInterval(autoPlayInterval);
            }
        
            // Pause autoplay on hover (good user experience)
            if (sliderImages) {
                sliderImages.addEventListener('mouseenter', stopAutoPlay);
                sliderImages.addEventListener('mouseleave', startAutoPlay);
            }
        
            // --- Initialize Slider ---
            createDots(); // Create dots when page loads
            goToSlide(0); // Ensure first slide is shown
            startAutoPlay(); // Start autoplay
        });