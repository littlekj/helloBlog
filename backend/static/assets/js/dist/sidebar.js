/**
 * Expand or close the sidebar in mobile screens.
 */

// 定义一个自定义属性，用于标记侧边栏的显示状态
const ATTR_DISPLAY = 'sidebar-display';

class SidebarUtil {
  // 静态属性，用于跟踪侧边栏是否处于展开状态
  static isExpanded = false;

  /**
   * 展开侧边栏
   */
  static expand() {
    if (!SidebarUtil.isExpanded) {
      // 向 body 元素添加一个自定义属性，标记侧边栏已展开
      document.body.setAttribute(ATTR_DISPLAY, '');
      SidebarUtil.isExpanded = true; // 更新状态为已展开
    }
  }

  /**
   * 收起侧边栏
   */
  static collapse() {
    if (SidebarUtil.isExpanded) {
      // 从 body 元素移除自定义属性，标记侧边栏已收起
      document.body.removeAttribute(ATTR_DISPLAY);
      SidebarUtil.isExpanded = false; // 更新状态为已收起
    }
  }

  /**
   * 切换侧边栏的显示状态
   */
  static toggle() {
    // 如果侧边栏是展开的，则收起；如果是收起的，则展开
    SidebarUtil.isExpanded ? SidebarUtil.collapse() : SidebarUtil.expand();
  }
}

/**
 * 为触发按钮和遮罩层添加点击事件监听器，以控制侧边栏的展开和收起
 */
export function sidebarExpand() {
  // 获取侧边栏触发按钮和遮罩层的 DOM 元素
  const trigger = document.getElementById('sidebar-trigger');
  const mask = document.getElementById('mask');

  // 如果触发按钮和遮罩层都存在，则添加点击事件监听器
  if (trigger && mask) {
    // 点击触发按钮时，切换侧边栏状态
    trigger.addEventListener('click', SidebarUtil.toggle);

    // 点击遮罩层时，收起侧边栏
    mask.addEventListener('click', SidebarUtil.toggle);
  }
}

// 立即调用函数，确保页面加载时绑定事件
document.addEventListener('DOMContentLoaded', () => {
  sidebarExpand();
});