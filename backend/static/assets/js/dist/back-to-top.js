/**
 * Reference: https://bootsnipp.com/snippets/featured/link-to-top-page
 */

function back2top() {
  const btn = document.getElementById('back-to-top');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      btn.classList.add('show');
    } else {
      btn.classList.remove('show');
    }
  });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0 });
  });
}

/* 在 DOM 完全加载后调用 back2top 函数 */
document.addEventListener('DOMContentLoaded', back2top);