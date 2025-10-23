// 主要交互功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initNavigation();
    initMobileMenu();
    initPageTransitions();
    initScrollEffects();
    initDownloadButtons();
});

// 导航功能
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    // 设置当前页面高亮
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage || (currentPage === '' && href === 'index.html')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // 添加点击事件
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // 如果是锚点链接，使用默认行为
            if (href && href.startsWith('#')) {
                // 让锚点链接使用默认行为，不阻止
                return;
            }
            
            // 对于其他链接，阻止默认行为并处理
            e.preventDefault();
            
            // 添加页面切换动画
            document.body.classList.add('page-transition');
            
            // 延迟跳转以显示动画
            setTimeout(() => {
                if (href && href !== 'null' && href !== '') {
                    window.location.href = href;
                }
            }, 300);
        });
    });
}

// 移动端菜单功能
function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            this.classList.toggle('active');
            navMenu.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
        
        // 点击菜单项后关闭菜单
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
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
}

// 页面切换动画
function initPageTransitions() {
    // 页面加载时添加淡入动画
    document.body.classList.add('page-transition');
    
    // 移除动画类
    setTimeout(() => {
        document.body.classList.remove('page-transition');
    }, 500);
}

// 滚动效果
function initScrollEffects() {
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // 导航栏滚动效果
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // 向下滚动，隐藏导航栏
            navbar.style.transform = 'translateY(-100%)';
        } else {
            // 向上滚动，显示导航栏
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });
    
    // 滚动到顶部按钮
    createScrollToTopButton();
}

// 创建滚动到顶部按钮
function createScrollToTopButton() {
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '↑';
    scrollBtn.className = 'scroll-to-top';
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #8b5cf6;
        color: white;
        border: none;
        font-size: 20px;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
    `;
    
    document.body.appendChild(scrollBtn);
    
    // 显示/隐藏按钮
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollBtn.style.opacity = '1';
            scrollBtn.style.visibility = 'visible';
        } else {
            scrollBtn.style.opacity = '0';
            scrollBtn.style.visibility = 'hidden';
        }
    });
    
    // 点击滚动到顶部
    scrollBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // 悬停效果
    scrollBtn.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.1)';
        this.style.background = '#7c3aed';
    });
    
    scrollBtn.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
        this.style.background = '#8b5cf6';
    });
}

// 下载按钮功能
function initDownloadButtons() {
    const downloadButtons = document.querySelectorAll('.download-btn-platform');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const platform = this.querySelector('span').textContent;
            
            // 添加点击动画
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // 显示下载提示
            showDownloadModal(platform);
        });
    });
    
    // 导航栏下载按钮 - 已禁用弹窗功能
    // const navDownloadBtn = document.querySelector('.nav-menu .download-btn');
    // if (navDownloadBtn) {
    //     navDownloadBtn.addEventListener('click', function() {
    //         showDownloadModal('客户端');
    //     });
    // }
}

// 显示下载模态框
function showDownloadModal(platform) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'download-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(26, 26, 46, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        max-width: 400px;
        width: 90%;
        transform: scale(0.8);
        transition: transform 0.3s ease;
    `;
    
    modalContent.innerHTML = `
        <h3 style="color: #ffffff; margin-bottom: 20px; font-size: 1.5rem;">下载 ${platform}</h3>
        <p style="color: #e5e7eb; margin-bottom: 30px; line-height: 1.6;">
            感谢您选择 OpenChat！<br>
            下载将很快开始。
        </p>
        <button class="modal-close-btn" style="
            background: #8b5cf6;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
        ">确定</button>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // 显示动画
    setTimeout(() => {
        modal.style.opacity = '1';
        modalContent.style.transform = 'scale(1)';
    }, 10);
    
    // 关闭模态框
    const closeModal = () => {
        modal.style.opacity = '0';
        modalContent.style.transform = 'scale(0.8)';
        setTimeout(() => {
            document.body.removeChild(modal);
        }, 300);
    };
    
    // 点击确定按钮关闭
    modalContent.querySelector('.modal-close-btn').addEventListener('click', closeModal);
    
    // 点击背景关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // ESC键关闭
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);
}

// 功能导航切换（多元兼容页面）
function initFeatureNavigation() {
    const featureNavItems = document.querySelectorAll('.feature-nav-item');
    
    featureNavItems.forEach(item => {
        item.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有活动状态
            featureNavItems.forEach(navItem => {
                navItem.classList.remove('active');
            });
            
            // 隐藏所有内容区域
            const allTabContents = document.querySelectorAll('.tab-content');
            allTabContents.forEach(content => {
                content.classList.remove('active');
            });
            
            // 添加当前活动状态
            this.classList.add('active');
            
            // 显示对应的内容区域
            const targetContent = document.getElementById(tabId + '-content');
            if (targetContent) {
                targetContent.classList.add('active');
            }
            
            // 添加点击动画
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

// 网格项目点击功能（免费开源页面）
function initGridItems() {
    const gridItems = document.querySelectorAll('.grid-item');
    
    gridItems.forEach(item => {
        item.addEventListener('click', function() {
            const text = this.querySelector('span').textContent;
            
            // 添加点击动画
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // 处理不同类型的点击
            if (text.includes('Windows') || text.includes('Mac')) {
                showDownloadModal(text);
            } else {
                showCommunityModal(text);
            }
        });
    });
}

// 显示社区链接模态框
function showCommunityModal(platform) {
    const modal = document.createElement('div');
    modal.className = 'community-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(26, 26, 46, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        max-width: 400px;
        width: 90%;
        transform: scale(0.8);
        transition: transform 0.3s ease;
    `;
    
    modalContent.innerHTML = `
        <h3 style="color: #ffffff; margin-bottom: 20px; font-size: 1.5rem;">${platform} 社区</h3>
        <p style="color: #e5e7eb; margin-bottom: 30px; line-height: 1.6;">
            欢迎加入我们的 ${platform} 社区！<br>
            在这里您可以获取最新资讯、参与讨论和获得技术支持。
        </p>
        <button class="modal-close-btn" style="
            background: #8b5cf6;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
        ">确定</button>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // 显示动画
    setTimeout(() => {
        modal.style.opacity = '1';
        modalContent.style.transform = 'scale(1)';
    }, 10);
    
    // 关闭模态框
    const closeModal = () => {
        modal.style.opacity = '0';
        modalContent.style.transform = 'scale(0.8)';
        setTimeout(() => {
            document.body.removeChild(modal);
        }, 300);
    };
    
    modalContent.querySelector('.modal-close-btn').addEventListener('click', closeModal);
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// 页面特定功能初始化
document.addEventListener('DOMContentLoaded', function() {
    // 根据当前页面初始化特定功能
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    if (currentPage === 'compatibility.html' || currentPage === 'index.html') {
        initFeatureNavigation();
    } else if (currentPage === 'opensource.html') {
        initGridItems();
    }
});

// 工具函数
const utils = {
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 检查元素是否在视口中
    isInViewport: function(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
};

// 显示二维码模态框
function showQRModal() {
    const modal = document.getElementById('qr-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

// 最简单的模态框测试
function showSimpleModal() {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    `;
    
    content.innerHTML = `
        <h3>测试模态框</h3>
        <p>这是一个简单的测试模态框</p>
        <button onclick="this.parentElement.parentElement.remove()">关闭</button>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
}

// 显示二维码模态框
function showQRCodeModal(event) {
    // 立即阻止所有默认行为
    if (event) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
    }
    
    // 防止任何可能的导航
    if (event) {
        event.returnValue = false;
    }
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'qr-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'qr-modal-content';
    modalContent.style.cssText = `
        background: rgba(26, 26, 46, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        max-width: 400px;
        width: 90%;
        transform: scale(0.8);
        transition: transform 0.3s ease;
        backdrop-filter: blur(10px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    `;
    
    modalContent.innerHTML = `
        <h3 style="color: #ffffff; margin-bottom: 20px; font-size: 1.5rem;">扫码加入社群</h3>
        <div style="width: 300px; height: 300px; background: #f0f0f0; border: 2px dashed #ccc; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; border-radius: 10px;">
            <p style="color: #666; font-size: 14px;">二维码图片位置</p>
        </div>
        <p style="color: #e5e7eb; margin-bottom: 20px; line-height: 1.6;">
            扫描二维码加入我们的社群<br>
            获取最新资讯和技术支持
        </p>
        <button class="qr-close-btn" style="
            background: #8b5cf6;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            font-family: inherit;
        ">关闭</button>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // 显示动画
    setTimeout(() => {
        modal.style.opacity = '1';
        modalContent.style.transform = 'scale(1)';
    }, 10);
    
    // 关闭模态框
    const closeQRModal = () => {
        modal.style.opacity = '0';
        modalContent.style.transform = 'scale(0.8)';
        setTimeout(() => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
        }, 300);
    };
    
    // 点击关闭按钮关闭
    modalContent.querySelector('.qr-close-btn').addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        closeQRModal();
        return false;
    });
    
    // 暂时移除背景点击和ESC键功能，避免干扰
    // modal.addEventListener('click', function(e) {
    //     if (e.target === modal) {
    //         closeQRModal();
    //     }
    // });
    
    // const handleEsc = (e) => {
    //     if (e.key === 'Escape') {
    //         closeQRModal();
    //         document.removeEventListener('keydown', handleEsc);
    //     }
    // };
    // document.addEventListener('keydown', handleEsc);
}

// 初始化社群按钮
function initCommunityButton() {
    const communityBtn = document.getElementById('community-btn');
    if (communityBtn) {
        communityBtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            showQRCodeModal(event);
            return false;
        });
        
        // 添加键盘支持
        communityBtn.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                showQRCodeModal(event);
                return false;
            }
        });
    }
}