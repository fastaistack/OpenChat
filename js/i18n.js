(function () {
  const STORAGE_KEY = 'openchat_lang'; // 'zh' | 'en'
  const $ = (sel) => document.querySelector(sel);

  // 智能设置文本：有 \n 时用 <br>，否则纯文本
  function applyTextToEl(el, val) {
    if (!el) return;
    if (typeof val !== 'string') {
      el.textContent = val == null ? '' : String(val);
      return;
    }
    if (val.includes('\n')) {
      el.innerHTML = val.replace(/\n/g, '<br>');
    } else {
      el.textContent = val;
    }
  }

  // 按选择器设置（单个）
  function setBySelector(selector, val) {
    const el = $(selector);
    applyTextToEl(el, val);
  }

  // 按 data-key 设置（可多个）
  function setByDataKey(key, val) {
    const list = document.querySelectorAll(`[data-key="${key}"]`);
    if (list.length === 0) return false; // 告诉上层没命中
    list.forEach((el) => applyTextToEl(el, val));
    return true;
  }

  const MAP = {
    zh: {
      __lang: 'zh-CN',
      __title: 'OpenChat - 开源免费AI解决方案',

      // 顶部导航
      '.nav-logo .logo-text': 'OpenChat',
      '.nav-menu .nav-link:nth-child(1)': '文档',
      '.nav-menu .community-btn': '社群',
      '.nav-menu a.nav-link[href="#faq"]': 'FAQ',
      '.download-dropdown .download-btn': '下载客户端',

      // 首页顶部下载（按钮文本，使用 data-key 或兜底）
      download_windows: 'Windows 下载',
      download_mac_m: 'Mac M系列 下载',

      // 旧的下载菜单（右侧“下载客户端”里的三项）
      '.download-menu a:nth-child(1) span': 'Windows',
      '.download-menu a:nth-child(2) span': 'Mac M系列',
      '.download-menu a:nth-child(3) span': 'Mac Intel',

      // 首页 hero
      '.hero-title h1': 'OpenChat',
      '.hero-description':
        '开源免费的AI解决方案,保护您的数据安全,提供强大的文档处理和智能助手功能\n无需注册!即可开启您的大模型体验!!',
      '.download-buttons a:nth-child(3) span': 'Mac Intel 下载',

      // 第二屏 tabs
      '.feature-nav .feature-nav-item[data-tab="compatibility"] span': '多元兼容',
      '.feature-nav .feature-nav-item[data-tab="security"] span': '安全部署',
      '.feature-nav .feature-nav-item[data-tab="plugins"] span': '实用插件',
      '.feature-nav .feature-nav-item[data-tab="models"] span': '模型应用',

      // 多元兼容内容
      '#compatibility-content .content-title h1': 'OpenChat兼容主流云端大模型',
      '#compatibility-content .content-description':
        '无论是 OpenAI 的强大语言理解能力,还是 Deepseek 的高效推理性能,亦或是硅基流动的创新技术,都能无缝接入;无需在不同平台间切换便能享体验所有模型服务',

      // 安全部署内容
      '#security-content .content-title h1': 'OpenChat安全部署解决方案',
      '#security-content .content-description':
        '采用企业级安全架构设计,支持本地化部署和私有云部署;数据全程加密传输,确保用户隐私安全;提供完整的权限管理和审计日志,满足企业合规要求',

      // 实用插件内容
      '#plugins-content .content-title h1': 'OpenChat实用插件生态',
      '#plugins-content .content-description':
        '丰富的插件生态支持,涵盖文档处理、代码生成、数据分析等多个领域;支持自定义插件开发,满足个性化需求;插件市场提供海量优质插件,一键安装即可使用',

      // 模型应用内容
      '#models-content .content-title h1': 'OpenChat智能模型应用',
      '#models-content .content-description':
        '集成多种先进AI模型,支持文本生成、图像识别、语音处理等智能应用;模型自动优化和调参,确保最佳性能表现;支持模型微调和定制训练,满足专业应用需求',

      // 开源页
      '.opensource-title h1': '免费开源',
      '.opensource-description':
        'OpenChat面相社会开源开放,您不仅可以免费使用本软件,也能在开源网站上看到我们的开发进度,若您有任何疑问和建议,欢迎通过社群与我们联系!',
      '.opensource-grid .grid-section a:nth-child(1) span': 'GitHub',
      '.opensource-grid .grid-section a:nth-child(2) span': 'Gitee',
      '.opensource-grid .grid-section a:nth-child(3) span': '小红书',

      // FAQ
      '#faq .faq-title h1': '常见问题',
      '.faq-list .faq-item:nth-child(1) .faq-question span': 'OpenChat会收集我的数据吗？',
      '.faq-list .faq-item:nth-child(1) .faq-answer p':
        '我们仅会收集下载次数用于统计，您使用中形成的任何数据我们不会进行收集。',
      '.faq-list .faq-item:nth-child(2) .faq-question span': '我的电脑需要什么配置才能使用OpenChat？',
      '.faq-list .faq-item:nth-child(2) .faq-answer p:nth-child(1)':
        'Windows版OpenChat适用于安装了64位Windows10与11系统的电脑并拥有8GB以上内存空间。',
      '.faq-list .faq-item:nth-child(2) .faq-answer p:nth-child(2)':
        'Mac版OpenChat适用于任何系统版本的MAC（M芯片），以及MACOS在12.5以上的MAC（Intel芯片）',
      '.faq-list .faq-item:nth-child(3) .faq-question span': '如何反馈使用中的问题？',
      '.faq-list .faq-item:nth-child(3) .faq-answer p':
        '您可以通过在开源社区留言、私信我们的小红书账号，或通过扫描二维码进入我们的粉丝群与我们取得联系。',
      '.faq-list .faq-item:nth-child(4) .faq-question span': 'OpenChat如何收取费用？',
      '.faq-list .faq-item:nth-child(4) .faq-answer p':
        'OpenChat本身无需注册且不收取任何费用，但部分服务通过第三方API提供（例如使用云端模型或第三方搜索引擎），使用时您可能需要向API提供者支付费用。',
      '.faq-list .faq-item:nth-child(5) .faq-question span': 'OpenChat适用于哪些场景？',
      '.faq-list .faq-item:nth-child(5) .faq-answer p':
        'OpenChat支持使用接入不同大模型解决各类问题，支持在本地部署0.5B-7B的小参数模型在私密的场景完成简单任务，也可以接入云端的万亿参数模型解决复杂问款，或使用智能助手来生成特定风格的内容，亦或者使用AI翻译功能翻译您的文件。',

      // 页脚
      '.copyright p': '© 2025 OpenChat - 开源私有AI助手',

      // 二维码弹窗
      '#qr-modal h3': '扫码加入社群',
      '#qr-modal p': '扫描二维码加入我们的社群\n获取最新资讯和技术支持',
      '#qr-modal button': '关闭',

      back_home: '返回首页',
      docs_nav_title: '文档导航',
      doc_intro: '项目简介',
      user_guide: '使用手册',
      mac_fix: 'MacOS拦截修复指南',
    },

    en: {
      __lang: 'en',
      __title: 'OpenChat - Free & Open-Source AI Suite',

      // 首页顶部下载（按钮文本，使用 data-key 或兜底）
      download_windows: 'Download for Windows',
      download_mac_m: 'Download for Mac  M series',

      // Top nav
      '.nav-logo .logo-text': 'OpenChat',
      '.nav-menu .nav-link:nth-child(1)': 'Docs',
      '.nav-menu .community-btn': 'Community',
      '.nav-menu a.nav-link[href="#faq"]': 'FAQ',
      '.download-dropdown .download-btn': 'Download',

      // 旧的下载菜单（右侧“下载客户端”里的三项）
      '.download-menu a:nth-child(1) span': 'Windows',
      '.download-menu a:nth-child(2) span': 'Mac M series',
      '.download-menu a:nth-child(3) span': 'Mac (Intel)',

      // Hero
      '.hero-title h1': 'OpenChat',
      '.hero-description':
        'Free & open-source AI suite focused on data privacy, powerful document workflows, and smart assistants.\nNo sign-up required—start your LLM journey now!',
      '.download-buttons a:nth-child(3) span': 'Download for Mac (Intel)',

      // Tabs
      '.feature-nav .feature-nav-item[data-tab="compatibility"] span': 'Compatibility',
      '.feature-nav .feature-nav-item[data-tab="security"] span': 'Secure Deploy',
      '.feature-nav .feature-nav-item[data-tab="plugins"] span': 'Plugins',
      '.feature-nav .feature-nav-item[data-tab="models"] span': 'Models',

      // Compatibility content
      '#compatibility-content .content-title h1': 'OpenChat works with major cloud LLMs',
      '#compatibility-content .content-description':
        'Seamlessly connect OpenAI, DeepSeek, SiliconFlow and more—enjoy all model services without switching platforms.',

      // Security content
      '#security-content .content-title h1': 'Enterprise-grade secure deployment',
      '#security-content .content-description':
        'Local or private-cloud deployment, end-to-end encrypted transport, fine-grained access control and audit logs for compliance.',

      // Plugins content
      '#plugins-content .content-title h1': 'Practical plugin ecosystem',
      '#plugins-content .content-description':
        'Rich plugins for docs, code, and analytics. Build custom plugins and install from the marketplace in one click.',

      // Models content
      '#models-content .content-title h1': 'Intelligent model applications',
      '#models-content .content-description':
        'Text, vision, and speech supported. Auto-tuning for optimal performance, plus fine-tuning and custom training.',

      // Open-source page
      '.opensource-title h1': 'Open Source & Free',
      '.opensource-description':
        'OpenChat is open to the community. Use it for free, track progress on our repos, and reach us via community channels for support.',
      '.opensource-grid .grid-section a:nth-child(1) span': 'GitHub',
      '.opensource-grid .grid-section a:nth-child(2) span': 'Gitee',
      '.opensource-grid .grid-section a:nth-child(3) span': 'Red Book',

      // FAQ
      '#faq .faq-title h1': 'FAQ',
      '.faq-list .faq-item:nth-child(1) .faq-question span': 'Does OpenChat collect my data?',
      '.faq-list .faq-item:nth-child(1) .faq-answer p':
        'We only count downloads for statistics. We do not collect any of your in-app data.',
      '.faq-list .faq-item:nth-child(2) .faq-question span': 'What are the system requirements?',
      '.faq-list .faq-item:nth-child(2) .faq-answer p:nth-child(1)':
        'Windows: 64-bit Windows 10/11 with at least 8 GB RAM.',
      '.faq-list .faq-item:nth-child(2) .faq-answer p:nth-child(2)':
        'Mac: Any macOS on Apple Silicon; or macOS 12.5+ for Intel-based Macs.',
      '.faq-list .faq-item:nth-child(3) .faq-question span': 'How can I give feedback or get help?',
      '.faq-list .faq-item:nth-child(3) .faq-answer p':
        'Leave an issue on our repos, DM us on Red Book, or scan the QR code to join our user group.',
      '.faq-list .faq-item:nth-child(4) .faq-question span': 'How is OpenChat priced?',
      '.faq-list .faq-item:nth-child(4) .faq-answer p':
        'OpenChat is free and requires no sign-up. Some features rely on third-party APIs (cloud LLMs, web search) that may incur provider fees.',
      '.faq-list .faq-item:nth-child(5) .faq-question span': 'What scenarios is OpenChat good for?',
      '.faq-list .faq-item:nth-child(5) .faq-answer p':
        'Use local 0.5B–7B models for private simple tasks, or connect trillion-parameter cloud LLMs for complex work. Assistants generate styled content, and AI Translate supports your documents.',

      // Footer
      '.copyright p': '© 2025 OpenChat — Private AI Assistant, Open Source',

      // QR modal
      '#qr-modal h3': 'Join the Community',
      '#qr-modal p': 'Scan the QR code to join\nGet the latest news and support',
      '#qr-modal button': 'Close',

      back_home: 'Back to Home',
      docs_nav_title: 'Documentation',
      doc_intro: 'Project Overview',
      user_guide: 'User Guide',
      mac_fix: 'macOS Security & Fix Guide',
    }
  };

  function applyLang(lang) {
    const dict = MAP[lang] || MAP.zh;

    // 文档级
    document.documentElement.setAttribute('lang', dict.__lang);
    document.title = dict.__title;

    // 遍历键：选择器 or data-key
    Object.entries(dict).forEach(([key, val]) => {
      if (key.startsWith('__')) return;

      if (key.startsWith('.') || key.startsWith('#')) {
        // 选择器键
        setBySelector(key, val);
      } else {
        // 数据键（优先 data-key 渲染）
        const hit = setByDataKey(key, val);
        if (!hit) {
          // —— 兜底：适配你现在的 DOM 结构（无需改 HTML）——
          // 顶部两个下载大按钮：.download-button-group 内第 1、2 个 <span>
          if (key === 'download_windows' || key === 'download_mac_m') {
            const spans = document.querySelectorAll('.download-button-group .download-btn-platform span');
            // 0 -> Windows, 1 -> Mac M 芯片
            if (spans[0] && key === 'download_windows') applyTextToEl(spans[0], dict.download_windows);
            if (spans[1] && key === 'download_mac_m') applyTextToEl(spans[1], dict.download_mac_m);
          }
        }
      }
    });

    // 滑块按钮状态（#lang-toggle 是一个 div）
    const btn = $('#lang-toggle');
    if (btn) {
      if (lang === 'en') btn.classList.add('active');
      else btn.classList.remove('active');
    }

    // ✅ 通知文档区：当前语言变了，重载当前 md
    if (typeof window.updateDocsForLang === 'function') {
      window.updateDocsForLang(lang);
    }
  }



  // 初始化
  const current = localStorage.getItem(STORAGE_KEY) || 'zh';
  applyLang(current);

  // 切换事件
  const toggle = $('#lang-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      const cur = localStorage.getItem(STORAGE_KEY) || 'zh';
      const next = (cur === 'zh') ? 'en' : 'zh';
      localStorage.setItem(STORAGE_KEY, next);
      applyLang(next);
    });
  }
})();
