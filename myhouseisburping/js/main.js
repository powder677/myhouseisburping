document.addEventListener('DOMContentLoaded', () => {
    console.log('MyHouseIsBurping.com loaded successfully.');

    // Mobile Navigation Toggle
    // This looks for a button with class "menu-toggle" and a nav list with class "nav-menu"
    const menuToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            // Toggles the 'active' class to show/hide the menu
            menuToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
            
            // Accessibility: Update aria-expanded
            const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
            menuToggle.setAttribute('aria-expanded', !isExpanded);
        });
    }

    // Optional: Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (navMenu && navMenu.classList.contains('active')) {
            if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        }
    });
});