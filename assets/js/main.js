/* 九原吉祥门窗服务 · 交互脚本 */
(function () {
  'use strict';

  var docEl = document.documentElement;
  docEl.classList.add('js');

  /* ---------- 移动导航 ---------- */
  var navToggle = document.getElementById('navToggle');
  var navLinks = document.getElementById('navLinks');

  function closeMenu() {
    if (!navLinks) return;
    navLinks.classList.remove('is-open');
    if (navToggle) {
      navToggle.setAttribute('aria-expanded', 'false');
      navToggle.setAttribute('aria-label', '打开菜单');
      navToggle.innerHTML = '<svg class="icon"><use href="#i-menu"/></svg>';
    }
  }

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', function () {
      var open = navLinks.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单');
      navToggle.innerHTML = '<svg class="icon"><use href="#' + (open ? 'i-close' : 'i-menu') + '"/></svg>';
    });
    navLinks.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
    document.addEventListener('click', function (e) {
      if (navLinks.classList.contains('is-open') &&
          !navLinks.contains(e.target) && !navToggle.contains(e.target)) {
        closeMenu();
      }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 960) closeMenu();
    });
  }

  /* ---------- 导航阴影 / 返回顶部 ---------- */
  var header = document.getElementById('header');
  var toTop = document.getElementById('toTop');

  function onScroll() {
    var y = window.pageYOffset || document.documentElement.scrollTop;
    if (header) header.classList.toggle('is-scrolled', y > 8);
    if (toTop) toTop.classList.toggle('is-show', y > 500);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- 滚动出现动画 ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- 复制号码 ---------- */
  var toast = document.getElementById('toast');
  var toastTimer;

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('is-show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('is-show'); }, 2200);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try {
        var ok = document.execCommand('copy');
        document.body.removeChild(ta);
        ok ? resolve() : reject(new Error('copy failed'));
      } catch (err) {
        document.body.removeChild(ta);
        reject(err);
      }
    });
  }

  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var num = btn.getAttribute('data-copy');
      copyText(num).then(function () {
        showToast('号码已复制：' + num);
        var old = btn.innerHTML;
        btn.innerHTML = '<svg class="icon"><use href="#i-check"/></svg>已复制';
        setTimeout(function () { btn.innerHTML = old; }, 1800);
      }).catch(function () {
        showToast('请长按号码手动复制：' + num);
      });
    });
  });

  /* ---------- 常见问题：同一时间只展开一条 ---------- */
  var faqs = document.querySelectorAll('.faq');
  faqs.forEach(function (item) {
    item.addEventListener('toggle', function () {
      if (item.open) {
        faqs.forEach(function (other) {
          if (other !== item) other.open = false;
        });
      }
    });
  });

  /* ---------- 施工实拍：点击放大 + 左右切换 ---------- */
  (function () {
    var cards = Array.prototype.slice.call(document.querySelectorAll('.work-card'));
    var qrCards = Array.prototype.slice.call(document.querySelectorAll('.qr-card'));
    var lb = document.getElementById('lb');
    if ((!cards.length && !qrCards.length) || !lb) return;

    var group = cards;  // 当前可切换的一组图

    var img = document.getElementById('lbImg');
    var cap = document.getElementById('lbCap');
    var idx = 0;
    var lastFocus = null;

    function show(i) {
      idx = (i + group.length) % group.length;
      var card = group[idx];
      lb.classList.toggle('is-single', group.length < 2);
      var pic = card.querySelector('img');
      if (!pic) return;
      img.src = pic.getAttribute('src');
      img.alt = pic.getAttribute('alt') || '';
      cap.textContent = card.getAttribute('data-cap') || '';
      lb.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    }

    function hide() {
      lb.classList.remove('is-open');
      group = cards;
      document.body.style.overflow = '';
      img.removeAttribute('src');
      if (lastFocus) lastFocus.focus();
    }

    cards.forEach(function (card, i) {
      card.addEventListener('click', function () {
        lastFocus = card;
        group = cards;
        show(i);
      });
    });

    /* 微信二维码：单张查看，不参与左右翻 */
    qrCards.forEach(function (card) {
      card.addEventListener('click', function () {
        lastFocus = card;
        group = qrCards;
        show(qrCards.indexOf(card));
      });
    });

    lb.addEventListener('click', function (e) {
      if (e.target === lb || (e.target.closest && e.target.closest('.lb__close'))) hide();
    });
    lb.querySelector('.lb__prev').addEventListener('click', function () { show(idx - 1); });
    lb.querySelector('.lb__next').addEventListener('click', function () { show(idx + 1); });

    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('is-open')) return;
      if (e.key === 'Escape') hide();
      else if (e.key === 'ArrowLeft') show(idx - 1);
      else if (e.key === 'ArrowRight') show(idx + 1);
    });

    var sx = 0;
    lb.addEventListener('touchstart', function (e) {
      sx = e.touches[0].clientX;
    }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 50) show(idx + (dx < 0 ? 1 : -1));
    }, { passive: true });
  })();

  /* ---------- 年份 ---------- */
  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();
})();
