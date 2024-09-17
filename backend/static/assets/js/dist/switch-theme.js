class ModeToggle {
  // 定义常量
  static get MODE_KEY() { return 'mode'; }
  static get MODE_ATTR() { return 'data-mode'; }
  static get DARK_MODE() { return 'dark'; }
  static get LIGHT_MODE() { return 'light'; }
  static get ID() { return 'mode-toggle'; }

  constructor() {
    // 监听系统颜色模式偏好变化
    this.sysDarkPrefers.addEventListener('change', this.handleSysPrefChange.bind(this));

    // 应用模式设置
    this.hasMode ? this.applyMode() : this.applyDefaultMode();

    // 页面加载时同步 Giscus 主题
    this.syncGiscusTheme();
  }

  // 系统是否偏好深色模式
  get sysDarkPrefers() {
    return window.matchMedia('(prefers-color-scheme: dark)');
  }

  // 系统偏好是否处于深色模式
  get isPreferDark() {
    return this.sysDarkPrefers.matches;
  }

  // 当前是否为深色模式
  get isDarkMode() {
    return this.mode === ModeToggle.DARK_MODE;
  }

  // 是否有自定义模式设置
  get hasMode() {
    return this.mode != null;
  }

  // 获取本地存储中的模式
  get mode() {
    return localStorage.getItem(ModeToggle.MODE_KEY);
  }

  // 获取当前模式
  get modeStatus() {
    return this.hasMode ? this.mode : (this.isPreferDark ? ModeToggle.DARK_MODE : ModeToggle.LIGHT_MODE);
  }

  // 处理系统颜色模式偏好变化
  handleSysPrefChange() {
    if (this.hasMode) {
      this.clearMode();
    }
    this.applyMode();
  }

  setDark() {
    document.documentElement.setAttribute(ModeToggle.MODE_ATTR, ModeToggle.DARK_MODE);
    localStorage.setItem(ModeToggle.MODE_KEY, ModeToggle.DARK_MODE);
    this.sendGiscusTheme('dark');  // 发送消息给 Giscus
  }

  setLight() {
    document.documentElement.setAttribute(ModeToggle.MODE_ATTR, ModeToggle.LIGHT_MODE);
    localStorage.setItem(ModeToggle.MODE_KEY, ModeToggle.LIGHT_MODE);
    this.sendGiscusTheme('light');  // 发送消息给 Giscus
  }

  clearMode() {
    document.documentElement.removeAttribute(ModeToggle.MODE_ATTR);
    localStorage.removeItem(ModeToggle.MODE_KEY);
  }

  // 应用当前模式
  applyMode() {
    if (this.isDarkMode) {
      this.setDark();
    } else {
      this.setLight();
    }
  }

  // 应用默认模式
  applyDefaultMode() {
    if (this.isPreferDark) {
      this.setDark();
    } else {
      this.setLight();
    }
  }

  // 切换模式
  flipMode() {
    if (this.isDarkMode) {
      this.setLight();
    } else {
      this.setDark();
    }
  }

  // 向 Giscus 发送主题变更消息
  sendGiscusTheme(theme) {
    const message = { setConfig: { theme: theme } };
    const giscusFrame = document.querySelector('.giscus-frame');
    // 本地环境允许任何来源，生产环境严格指定 giscus.app
    const giscusOrigin = window.location.hostname === '127.0.0.1' ? '*' : 'https://giscus.app';

    if (giscusFrame && giscusFrame.contentWindow) {
      // 确保 iframe 加载完成后发送消息
      giscusFrame.contentWindow.postMessage({ giscus: message }, giscusOrigin);
    } else {
      console.error('Giscus iframe not found or not ready.');
    }
  }

  // 页面加载时同步 Giscus 主题
  syncGiscusTheme() {
    const currentTheme = this.modeStatus === ModeToggle.DARK_MODE ? 'dark' : 'light';
    const giscusFrame = document.querySelector('.giscus-frame');

    if (giscusFrame) {
      giscusFrame.onload = () => {
        setTimeout(() => {
            this.sendGiscusTheme(currentTheme);
        }, 500);
      };
    } else {
      this.sendGiscusTheme(currentTheme);  // 如果 Giscus 已经加载，直接发送主题消息
    }
  }
}

// 页面加载完成时初始化 ModeToggle
document.addEventListener('DOMContentLoaded', () => {
  const modeToggle = new ModeToggle();
  const toggle = document.getElementById('mode-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      modeToggle.flipMode();
    });
  }
});
