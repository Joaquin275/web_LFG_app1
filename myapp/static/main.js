// Archivo: main.js - Scripts optimizados

document.addEventListener('DOMContentLoaded', function () {
  // ===== Modal de información del plato =====
  const cards = document.querySelectorAll('.clickable-card');
  const modal = new bootstrap.Modal(document.getElementById('infoPlatoModal'));

  cards.forEach(card => {
    card.addEventListener('click', function (event) {
      if (event.target.closest('form')) return;

      const fields = {
        nombre: 'infoPlatoModalLabel',
        descripcion: 'infoPlatoDescripcion',
        precio: 'infoPlatoPrecio',
        imagen: 'infoPlatoImagen',
        grupo: 'infoPlatoGrupo',
        kilogramos: 'infoPlatoKg',
        'vida-util': 'infoPlatoVidaUtil',
        calorias: 'infoPlatoCalorias',
        proteinas: 'infoPlatoProteinas',
        grasa: 'infoPlatoGrasa',
        carbohidratos: 'infoPlatoCarbohidratos',
        sodio: 'infoPlatoSodio',
        ingredientes: 'infoPlatoIngredientes',
        alergenos: 'infoPlatoAlergenos'
      };

      for (const [key, id] of Object.entries(fields)) {
        const element = document.getElementById(id);
        const value = card.getAttribute(`data-${key}`);

        if (key === 'imagen') {
          element.src = value || '';
          element.style.display = value ? 'block' : 'none';
        } else {
          element.textContent = value || 'No disponible';
        }
      }

      modal.show();
    });
  });

  // ===== Filtro visual por familia (no backend) =====
  const botones = document.querySelectorAll('.btn-familia');
  const grupos = document.querySelectorAll('.grupo-platos');

  botones.forEach(boton => {
    boton.addEventListener('click', () => {
      botones.forEach(b => b.classList.remove('active'));
      boton.classList.add('active');

      const familia = boton.dataset.familia;
      grupos.forEach(grupo => {
        grupo.style.display = (familia === 'todos' || grupo.dataset.familia === familia) ? 'block' : 'none';
      });
    });
  });
});

// ===== NAVBAR efecto shrink al hacer scroll =====
window.addEventListener('scroll', function () {
  const navbar = document.querySelector('.transition-navbar');
  if (window.scrollY > 10) {
    navbar.classList.add('navbar-shrink');
  } else {
    navbar.classList.remove('navbar-shrink');
  }
});
