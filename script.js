// Form validation
const form = document.querySelector('form');
form.addEventListener('submit', (e) => {
  e.preventDefault();
  // Add your form validation logic here
  // ...

  // Reset the form after successful submission
  form.reset();
});

// Smooth scrolling
const navLinks = document.querySelectorAll('nav ul li a');
navLinks.forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const targetId = e.target.getAttribute('href');
    const targetElement = document.querySelector(targetId);
    targetElement.scrollIntoView({ behavior: 'smooth' });
  });
});