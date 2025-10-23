// FAQ折叠功能

document.addEventListener('DOMContentLoaded', function() {
    initFAQ();
});

// 初始化FAQ功能
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    // 确保所有FAQ项目都有正确的宽度
    faqItems.forEach(item => {
        item.style.width = '100%';
        item.style.maxWidth = '1000px';
    });
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        const icon = item.querySelector('.faq-icon');
        
        if (question && answer && icon) {
            // 添加点击事件
            question.addEventListener('click', function() {
                toggleFAQ(item, answer, icon);
            });
            
            // 添加键盘支持
            question.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleFAQ(item, answer, icon);
                }
            });
            
            // 设置可访问性属性
            question.setAttribute('tabindex', '0');
            question.setAttribute('role', 'button');
            question.setAttribute('aria-expanded', item.classList.contains('active') ? 'true' : 'false');
            question.setAttribute('aria-controls', `faq-answer-${Array.from(faqItems).indexOf(item)}`);
            
            answer.setAttribute('id', `faq-answer-${Array.from(faqItems).indexOf(item)}`);
        }
    });
}

// 切换FAQ项目展开/折叠状态
function toggleFAQ(item, answer, icon) {
    const isActive = item.classList.contains('active');
    
    if (isActive) {
        // 折叠
        collapseFAQ(item, answer, icon);
    } else {
        // 展开
        expandFAQ(item, answer, icon);
    }
}

// 展开FAQ项目
function expandFAQ(item, answer, icon) {
    // 添加活动状态
    item.classList.add('active');
    
    // 更新可访问性属性
    const question = item.querySelector('.faq-question');
    question.setAttribute('aria-expanded', 'true');
    
    // 更新图标
    updateFAQIcon(icon, true);
    
    // 展开答案区域 - 使用更大的高度以容纳更多内容
    answer.style.maxHeight = '300px';
    
    // 确保宽度与默认展开项一致
    item.style.width = '100%';
    item.style.maxWidth = '1000px';
    
    
    // 添加展开动画
    answer.style.transition = 'max-height 0.3s ease, padding 0.3s ease';
    
    // 添加点击动画
    item.style.transform = 'scale(0.98)';
    setTimeout(() => {
        item.style.transform = 'scale(1)';
    }, 150);
    
    // 滚动到当前项目（如果不在视口中）
    setTimeout(() => {
        if (!isElementInViewport(item)) {
            item.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }, 100);
    
    // 检查并调整页面布局，确保内容不被遮挡
    setTimeout(() => {
        adjustPageLayoutForFAQ(item);
    }, 400);
}

// 折叠FAQ项目
function collapseFAQ(item, answer, icon) {
    // 移除活动状态
    item.classList.remove('active');
    
    // 更新可访问性属性
    const question = item.querySelector('.faq-question');
    question.setAttribute('aria-expanded', 'false');
    
    // 更新图标
    updateFAQIcon(icon, false);
    
    // 折叠答案区域
    answer.style.maxHeight = '0';
    
    // 重置宽度设置
    item.style.width = '100%';
    item.style.maxWidth = '1000px';
    
    // 添加点击动画
    item.style.transform = 'scale(0.98)';
    setTimeout(() => {
        item.style.transform = 'scale(1)';
    }, 150);
}

// 更新FAQ图标状态
function updateFAQIcon(icon, isExpanded) {
    if (isExpanded) {
        // 展开状态：显示向上箭头
        icon.src = 'images/icons/chevron-up-icon.svg';
        icon.alt = '折叠';
        icon.style.transform = 'rotate(0deg)';
    } else {
        // 折叠状态：显示向下箭头
        icon.src = 'images/icons/chevron-down-icon.svg';
        icon.alt = '展开';
        icon.style.transform = 'rotate(0deg)';
    }
    
    // 添加图标旋转动画
    icon.style.transition = 'transform 0.3s ease';
}

// 检查元素是否在视口中
function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// 键盘导航支持
document.addEventListener('keydown', function(e) {
    const faqItems = document.querySelectorAll('.faq-item');
    const activeElement = document.activeElement;
    
    // 检查是否在FAQ区域内
    if (activeElement && activeElement.closest('.faq-container')) {
        const currentIndex = Array.from(faqItems).findIndex(item => 
            item.querySelector('.faq-question') === activeElement
        );
        
        if (currentIndex !== -1) {
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    const nextIndex = (currentIndex + 1) % faqItems.length;
                    faqItems[nextIndex].querySelector('.faq-question').focus();
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    const prevIndex = currentIndex === 0 ? faqItems.length - 1 : currentIndex - 1;
                    faqItems[prevIndex].querySelector('.faq-question').focus();
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    faqItems[0].querySelector('.faq-question').focus();
                    break;
                    
                case 'End':
                    e.preventDefault();
                    faqItems[faqItems.length - 1].querySelector('.faq-question').focus();
                    break;
            }
        }
    }
});

// 搜索功能（可选）
function initFAQSearch() {
    // 创建搜索框
    const searchContainer = document.createElement('div');
    searchContainer.className = 'faq-search-container';
    searchContainer.style.cssText = `
        margin-bottom: 30px;
        text-align: center;
    `;
    
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = '搜索常见问题...';
    searchInput.className = 'faq-search-input';
    searchInput.style.cssText = `
        width: 100%;
        max-width: 400px;
        padding: 12px 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 25px;
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        font-size: 1rem;
        outline: none;
        transition: all 0.3s ease;
    `;
    
    searchContainer.appendChild(searchInput);
    
    // 插入到FAQ容器前
    const faqContainer = document.querySelector('.faq-container');
    if (faqContainer) {
        faqContainer.parentNode.insertBefore(searchContainer, faqContainer);
    }
    
    // 搜索功能
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const faqItems = document.querySelectorAll('.faq-item');
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question span').textContent.toLowerCase();
            const answer = item.querySelector('.faq-answer p').textContent.toLowerCase();
            
            if (question.includes(searchTerm) || answer.includes(searchTerm)) {
                item.style.display = 'block';
                item.style.opacity = '1';
            } else {
                item.style.display = 'none';
                item.style.opacity = '0';
            }
        });
    });
    
    // 搜索框样式
    searchInput.addEventListener('focus', function() {
        this.style.borderColor = '#8b5cf6';
        this.style.background = 'rgba(255, 255, 255, 0.15)';
    });
    
    searchInput.addEventListener('blur', function() {
        this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
        this.style.background = 'rgba(255, 255, 255, 0.1)';
    });
}

// 统计功能
function initFAQStats() {
    const faqItems = document.querySelectorAll('.faq-item');
    const statsContainer = document.createElement('div');
    statsContainer.className = 'faq-stats';
    statsContainer.style.cssText = `
        text-align: center;
        margin-bottom: 20px;
        color: #9ca3af;
        font-size: 0.9rem;
    `;
    
    statsContainer.textContent = `共 ${faqItems.length} 个常见问题`;
    
    // 插入到FAQ标题后
    const faqTitle = document.querySelector('.faq-title');
    if (faqTitle) {
        faqTitle.parentNode.insertBefore(statsContainer, faqTitle.nextSibling);
    }
}

// 自动展开第一个FAQ项目
function autoExpandFirst() {
    const firstFAQ = document.querySelector('.faq-item');
    if (firstFAQ && !firstFAQ.classList.contains('active')) {
        const answer = firstFAQ.querySelector('.faq-answer');
        const icon = firstFAQ.querySelector('.faq-icon');
        
        if (answer && icon) {
            expandFAQ(firstFAQ, answer, icon);
        }
    }
}

// 初始化所有FAQ功能
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否在FAQ页面
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    if (currentPage === 'faq.html' || currentPage === 'index.html') {
        // 可选功能
        // initFAQSearch();
        // initFAQStats();
        
        // 自动展开第一个项目
        // setTimeout(autoExpandFirst, 500);
    }
});

// 调整页面布局以适应FAQ展开
function adjustPageLayoutForFAQ(item) {
    const copyright = document.querySelector('.copyright');
    
    if (!copyright) return;
    
    const copyrightRect = copyright.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    
    // 计算FAQ项目底部到版权信息的距离
    const distanceToCopyright = copyrightRect.top - itemRect.bottom;
    
    // 如果距离太小（小于100px），调整页面滚动
    if (distanceToCopyright < 100) {
        const scrollAmount = 100 - distanceToCopyright + 50; // 额外50px缓冲
        window.scrollBy({
            top: scrollAmount,
            behavior: 'smooth'
        });
    }
}

// 导出功能供其他模块使用
window.FAQ = {
    init: initFAQ,
    toggle: toggleFAQ,
    expand: expandFAQ,
    collapse: collapseFAQ,
    search: initFAQSearch,
    stats: initFAQStats
};
