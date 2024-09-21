/**
 * 该脚本使 #search-result-wrapper 能够在加载和显示之间自动切换。
 */

// 获取一些页面上的 DOM 元素
const btnSbTrigger = document.getElementById('sidebar-trigger');  // 侧边栏触发按钮
const btnSearchTrigger = document.getElementById('search-trigger');  // 搜索触发按钮
const btnCancel = document.getElementById('search-cancel');  // 搜索取消按钮
const content = document.querySelectorAll('#main-wrapper>.container>.row');  // 主内容区域
const topbarTitle = document.getElementById('topbar-title');  // 顶部栏标题
const search = document.getElementById('search');  // 搜索栏容器
const resultWrapper = document.getElementById('search-result-wrapper');  // 搜索结果容器
const results = document.getElementById('search-results');  // 搜索结果内容
const input = document.getElementById('search-input');  // 搜索输入框
const hints = document.getElementById('search-hints');  // 搜索提示信息

// CSS 类名常量
const LOADED = 'd-block';  // 用于显示元素的类名
const UNLOADED = 'd-none';  // 用于隐藏元素的类名
const FOCUS = 'input-focus';  // 输入框获得焦点时的类名
const FLEX = 'd-flex';  // 用于显示 flex 布局的类名

let debounceTimer;  // 用于存储去抖动定时器
let query = '';  // 用于存储当前搜索的查询字符串
let currentPage = 1;

/* 在移动设备屏幕上的行为（侧边栏隐藏时） */
class MobileSearchBar {
  // 显示搜索栏并隐藏其他元素
  static on() {
    btnSbTrigger.classList.add(UNLOADED);  // 隐藏侧边栏触发按钮
    topbarTitle.classList.add(UNLOADED);  // 隐藏顶部栏标题
    btnSearchTrigger.classList.add(UNLOADED);  // 隐藏搜索触发按钮
    search.classList.add(FLEX);  // 显示搜索栏
    btnCancel.classList.add(LOADED);  // 显示取消按钮
  }

  // 隐藏搜索栏并恢复其他元素
  static off() {
    btnCancel.classList.remove(LOADED);  // 隐藏取消按钮
    search.classList.remove(FLEX);  // 隐藏搜索栏
    btnSbTrigger.classList.remove(UNLOADED);  // 显示侧边栏触发按钮
    topbarTitle.classList.remove(UNLOADED);  // 显示顶部栏标题
    btnSearchTrigger.classList.remove(UNLOADED);  // 显示搜索触发按钮
  }
}

// 发送 Ajax 请求获取特定页的数据
function fetchResults(query, page) {
//    console.log('Fetching results for query:', query);  // 添加调试
    fetch(`/search/?q=${encodeURIComponent(query)}&page=${page}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
//        console.log('Search data:', data.results);  // 打印数据
        if (data.results && data.results.length > 0) {  // 空数组 [] 在 JavaScript 中被视为 truthy 值，所以需要检查长度
            results.innerHTML = data.results_html;  // 显示当前页数据及更新分页链接
            ResultSwitch.on();
        } else {
            // 没有结果时显示提示信息
            ResultSwitch.off();
         }
    }).catch(error => {
        // 请求失败时的提示信息
        results.innerHTML = '<p class="row justify-content-center">搜索请求失败，请稍后再试</p>';
        console.error('搜索请求失败:', error);
    });
}

/* 切换搜索结果的显示与隐藏 */
class ResultSwitch {
  // 显示搜索结果
  static on() {
    if (isMobileView()) {
      hints.classList.add(UNLOADED);  // 隐藏提示信息          
    }
    content.forEach((el) => {
      el.classList.add(UNLOADED);  // 隐藏主内容区域
    });
    resultWrapper.classList.remove(UNLOADED);  // 显示搜索结果容器
  }

  // 隐藏搜索结果
  static off() {
    if (isMobileView()) {
      hints.classList.add(UNLOADED);  // 隐藏热门标签          
    }
    content.forEach((el) => {
      el.classList.add(UNLOADED);  // 隐藏主内容区域
    });
    resultWrapper.classList.remove(UNLOADED);  // 显示搜索结果容器
    results.innerHTML = '<p class="row justify-content-center">呜呜~没有找到结果</p>';
  }
}

// 判断当前是否处于移动视图（搜索栏是否处于显示状态）
function isMobileView() {
  return btnCancel.classList.contains(LOADED);  // 如果取消按钮处于显示状态，则表示在移动视图
}

// 定义导出的 displaySearch 函数，用于控制搜索栏和搜索结果的行为
function displaySearch() {
  // 监听搜索触发按钮的点击事件
  btnSearchTrigger.addEventListener('click', () => {
    MobileSearchBar.on();  // 显示搜索栏
    input.focus();  // 使搜索输入框获得焦点
    resultWrapper.classList.remove(UNLOADED);  // 显示搜索结果容器
    hints.classList.remove(UNLOADED);  // 显示热门标签
    content.forEach((el) => {
      el.classList.add(UNLOADED);  // 隐藏主内容区域
    });
  });

  // 监听取消按钮的点击事件
  btnCancel.addEventListener('click', () => {
    MobileSearchBar.off();  // 隐藏搜索栏
    input.value = '';  // 清空输入框内容
    results.innerHTML = '';  // 清空搜索结果
    if (isMobileView()) {
      hints.classList.remove(UNLOADED);    
    } else {
      resultWrapper.classList.add(UNLOADED);  // 隐藏搜索结果容器
      content.forEach((el) => {
        el.classList.remove(UNLOADED);  // 显示主内容区域
      });
    }
  });

  // 监听搜索输入框获得焦点的事件
  input.addEventListener('focus', () => {
    search.classList.add(FOCUS);  // 给搜索栏添加获得焦点的样式
  });

  // 监听搜索输入框失去焦点的事件
  input.addEventListener('focusout', () => {
    search.classList.remove(FOCUS);  // 移除搜索栏的焦点样式
  });

  // 监听搜索输入框内容变化的事件
  input.addEventListener('input', function() {
    // 设置去抖动 debounce 机制，防止用户快速输入时多次触发请求
    clearTimeout(debounceTimer);  // 清除上一次的定时器
    debounceTimer = setTimeout(function() {
      query = input.value.trim();  
      results.innerHTML = '';  // 避免未查询有历史搜索结果
      // 显示取消按钮
      btnCancel.classList.remove(UNLOADED);
      if (query.length > 0) {
        // 如果输入框不为空，请求搜索结果，如果不匹配显示提示信息
        currentPage = 1;  // 重置到第一页
        fetchResults(query, currentPage);  // 请求搜索结果    
      } else {
        // 如果输入框为空，清空搜索结果容器
        results.innerHTML = '';
        if (isMobileView()) {
          hints.classList.remove(UNLOADED);  // 移动端显示热门标签信息 
        } else {
          resultWrapper.classList.add(UNLOADED);
          content.forEach((el) => {
            el.classList.remove(UNLOADED);  // 电脑端显示主内容区域
          }); 
        } 
      } 
    }, 300);  // 延迟300毫秒发起请求
  });

  // 监听分页链接的点击事件
  resultWrapper.addEventListener('click', function(event) {
      // 使用 event delegation 确保捕捉到分页链接的点击事件
      const target = event.target.closest('.page-link');
      if (target) {
          event.preventDefault();  // 阻止默认行为，防止页面刷新，通过 Ajax 获取新页面内容
          const page = target.getAttribute('data-page');  // 获取分页的页码
          if (page) {
              currentPage = parseInt(page);
              // 发起分页请求，获取下一页的结果
              fetchResults(query, currentPage);
          }
      }
  });
}


// 调用搜索栏显示和搜索功能
document.addEventListener('DOMContentLoaded', () => {
  displaySearch();
});
