// 主要交互功能
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initMobileMenu();
    initPageTransitions();
    initScrollEffects();
    initDownloadButtons();
    initSectionSwitcher();
});

// ✅ 文档侧边栏切换逻辑
document.addEventListener('DOMContentLoaded', () => {
  const links = document.querySelectorAll('.docs-link');
  const sections = document.querySelectorAll('.doc-section');

  links.forEach(link => {
    link.addEventListener('click', () => {
      // 移除旧高亮
      links.forEach(l => l.classList.remove('active'));
      link.classList.add('active');

      // 隐藏所有内容区
      sections.forEach(sec => sec.style.display = 'none');

      // 显示目标
      const target = link.getAttribute('data-doc');
      const targetEl = document.getElementById(`doc-${target}`);
      if (targetEl) targetEl.style.display = 'block';
    });
  });
});

// 导航功能
function initNavigation() {
  // ✅ 只选真正的超链接，排除 button/div 等
  const navLinks = document.querySelectorAll('a.nav-link[href]');
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';

  // 当前页高亮
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // 只给“会跳页面的链接”加过渡效果
  navLinks.forEach(link => {
    // 忽略站内锚点（#...），让浏览器默认滚动；忽略 data-target 由我们自定义切换
    if (link.hasAttribute('data-target')) return;
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#')) return;

    link.addEventListener('click', function (e) {
      e.preventDefault();
      document.body.classList.add('page-transition');
      setTimeout(() => { window.location.href = href; }, 300);
    });
  });
}


function initSectionSwitcher() {
  const mainSections = document.getElementById('main-sections');
  const docsSection  = document.getElementById('docs');
  const docsBtn      = document.querySelector('.nav-link[data-target="docs"]');
  const logo         = document.getElementById('nav-logo');
  const backHomeBtn  = document.getElementById('back-home');
  if (!mainSections || !docsSection || !docsBtn) return;

  const enterDocs = () => {
    mainSections.style.display = 'none';
    docsSection.style.display  = 'block';
    document.body.classList.add('docs-mode');
    docsBtn.classList.add('active');     // ✅ 文档按钮与其它项同逻辑
    hookScrollToTopForDocs();
  };

  const leaveDocs = () => {
    docsSection.style.display  = 'none';
    mainSections.style.display = 'block';
    document.body.classList.remove('docs-mode');
    docsBtn.classList.remove('active');  // ✅ 退出时去掉
    hookScrollToTopForHome();
  };

  if (docsBtn) {
    docsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      enterDocs();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
  if (logo)        logo.addEventListener('click', leaveDocs);
  if (backHomeBtn) backHomeBtn.addEventListener('click', leaveDocs);
}


// 移动端菜单功能
function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    if (!hamburger || !navMenu) return;

    hamburger.addEventListener('click', function() {
        this.classList.toggle('active');
        navMenu.classList.toggle('active');
        document.body.classList.toggle('menu-open');
    });

    // 点击菜单项后关闭菜单
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
    });

    // 点击外部区域关闭菜单
    document.addEventListener('click', function(e) {
        if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });
}

// 页面切换动画
function initPageTransitions() {
    document.body.classList.add('page-transition');
    setTimeout(() => document.body.classList.remove('page-transition'), 500);
}

// 滚动效果
function initScrollEffects() {
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        navbar.style.transform = (scrollTop > lastScrollTop && scrollTop > 100)
          ? 'translateY(-100%)' : 'translateY(0)';
        lastScrollTop = scrollTop;
    });
    createScrollToTopButton();
}

// 创建滚动到顶部按钮
function createScrollToTopButton(target = window) {
  // 如果已有就不重复创建
  if (document.querySelector('.scroll-to-top')) return;

  const btn = document.createElement('button');
  btn.innerHTML = '↑';
  btn.className = 'scroll-to-top';
  btn.style.cssText = `
    position: fixed; bottom: 30px; right: 30px;
    width: 50px; height: 50px; border-radius: 50%;
    background: #8b5cf6; color: #fff; border: none;
    font-size: 20px; cursor: pointer; opacity: 0;
    visibility: hidden; transition: all .3s ease; z-index: 1000;
    box-shadow: 0 4px 12px rgba(139,92,246,.3);
  `;
  document.body.appendChild(btn);

  const onScroll = () => {
    const y = target === window ? window.pageYOffset : target.scrollTop;
    btn.style.opacity   = y > 300 ? '1' : '0';
    btn.style.visibility= y > 300 ? 'visible' : 'hidden';
  };

  // 绑定到目标
  (target === window ? window : target).addEventListener('scroll', onScroll);
  btn.addEventListener('click', () => {
    if (target === window) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      target.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  // hover 效果
  btn.addEventListener('mouseenter', function(){ this.style.transform='scale(1.1)'; this.style.background='#7c3aed'; });
  btn.addEventListener('mouseleave', function(){ this.style.transform='scale(1)';   this.style.background='#8b5cf6'; });
}

/* 在进入/离开文档时切换按钮的监听目标 */
function hookScrollToTopForDocs() {
  const docsContainer = document.querySelector('.docs-container');
  if (!docsContainer) return;
  // 先删旧的按钮再创建，避免重复
  const old = document.querySelector('.scroll-to-top');
  if (old) old.remove();
  createScrollToTopButton(docsContainer);
}

function hookScrollToTopForHome() {
  const old = document.querySelector('.scroll-to-top');
  if (old) old.remove();
  createScrollToTopButton(window);
}


// 下载按钮功能
function initDownloadButtons() {
    const buttons = document.querySelectorAll('.download-btn-platform');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            const platform = this.querySelector('span').textContent;
            this.style.transform = 'scale(0.95)';
            setTimeout(() => this.style.transform = 'scale(1)', 150);
            showDownloadModal(platform);
        });
    });
}

// 显示下载模态框
function showDownloadModal(platform) {
    const modal = document.createElement('div');
    modal.className = 'download-modal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.8); display: flex; justify-content: center;
        align-items: center; z-index: 2000; opacity: 0; transition: opacity 0.3s;
    `;
    const box = document.createElement('div');
    box.style.cssText = `
        background: rgba(26, 26, 46, 0.95); border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px; padding: 40px; text-align: center;
        max-width: 400px; width: 90%; transform: scale(0.8);
        transition: transform 0.3s ease;
    `;
    box.innerHTML = `
        <h3 style="color:#fff;margin-bottom:20px;">下载 ${platform}</h3>
        <p style="color:#e5e7eb;margin-bottom:30px;">感谢您选择 OpenChat！<br>下载将很快开始。</p>
        <button class="modal-close-btn" style="background:#8b5cf6;color:#fff;border:none;padding:12px 30px;border-radius:25px;cursor:pointer;">确定</button>
    `;
    modal.appendChild(box);
    document.body.appendChild(modal);
    setTimeout(() => { modal.style.opacity = '1'; box.style.transform = 'scale(1)'; }, 10);
    const close = () => { modal.style.opacity = '0'; box.style.transform = 'scale(0.8)'; setTimeout(() => document.body.removeChild(modal), 300); };
    box.querySelector('.modal-close-btn').addEventListener('click', close);
    modal.addEventListener('click', e => { if (e.target === modal) close(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
}
