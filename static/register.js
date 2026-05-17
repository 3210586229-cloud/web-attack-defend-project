const form = document.querySelector('form');
      const password = document.querySelector('input[name="password"]');
      const confirmPassword = document.querySelector('input[name="confirm_password"]');
      const errorMessage = document.querySelector('#password_error');

      form.addEventListener('submit', function (event) {
          if (password.value !== confirmPassword.value) {
              event.preventDefault();

              errorMessage.textContent = '两次密码不一致';
              confirmPassword.classList.add('input-error', 'shake');

              confirmPassword.addEventListener('animationend', function () {
                  confirmPassword.classList.remove('shake');
              }, { once: true });
          }
      });

      confirmPassword.addEventListener('input', function () {
          errorMessage.textContent = '';
          confirmPassword.classList.remove('input-error');
      });