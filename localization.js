// Antigravity zh-CN 2.15.1 — exact UI text matching; no IPC/network changes.
(() => {
  'use strict';
  if (globalThis.__antigravityZhCN) return;
  const dictionary = /*__DICTIONARY__*/ {};
  const own = (key) => Object.prototype.hasOwnProperty.call(dictionary, key);
  function translate(text) {
    if (typeof text !== 'string') return text;
    const key = text.trim();
    if (own(key)) return text.replace(key, dictionary[key]);
    // Anchored patterns preserve variable values and never truncate messages.
    const rules = [
      [/^Load older messages, showing (\d+) of (\d+)$/, '加载更早消息，当前显示 $1 / $2 条'],
      [/^(\d+) agents? running$/, '$1 个智能体正在运行'],
      [/^(\d+(?:\.\d+)?)% of the customization budget is available\.?$/, '自定义项预算剩余 $1%。'],
    ];
    for (const [pattern, replacement] of rules) {
      if (pattern.test(key)) return text.replace(key, key.replace(pattern, replacement));
    }
    return text;
  }

  // Observed 2.13.0 conversations use role=article rather than <article>.
  const protectedSelector = [
    'script', 'style', 'pre', 'code', 'textarea', 'input',
    '[contenteditable]:not([contenteditable="false"])', '.monaco-editor',
    '.cm-editor', '.xterm', 'article', '[role="article"]',
    '[translate="no"]', '[data-zh-cn-preserve]',
    'a[href^="/c/"]', 'iframe',
  ].join(',');
  function protectedText(element) {
    if (!element || element.closest(protectedSelector)) return true;
    // Project names are expandable sidebar buttons outside section headings.
    const button = element.closest('[role="navigation"] button[aria-expanded], nav button[aria-expanded]');
    return Boolean(button && !button.getAttribute('aria-label') && !button.closest('h1,h2,h3,[role="heading"]'));
  }
  function processNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (protectedText(node.parentElement)) return;
      const value = translate(node.nodeValue);
      if (node.nodeValue !== value) node.nodeValue = value;
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    // Input values and editable children are untouched; UI hints may translate.
    if (!node.closest('article,[role="article"],pre,code,[translate="no"],[data-zh-cn-preserve]')) {
      for (const attribute of ['placeholder', 'title', 'aria-label']) {
        const original = node.getAttribute(attribute);
        if (!original) continue;
        const value = translate(original);
        if (value !== original) node.setAttribute(attribute, value);
      }
    }
    if (protectedText(node)) return;
    for (const child of node.childNodes) processNode(child);
  }
  const pending = new Set();
  let scheduled = false;
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        for (const node of mutation.addedNodes) pending.add(node);
      } else pending.add(mutation.target);
    }
    if (!scheduled) {
      scheduled = true;
      queueMicrotask(() => {
        scheduled = false;
        const nodes = Array.from(pending);
        pending.clear();
        for (const node of nodes) if (node.isConnected) processNode(node);
      });
    }
  });
  function start() {
    if (!document.body) return;
    processNode(document.body);
    observer.observe(document.body, {
      childList: true, subtree: true, characterData: true,
      attributes: true, attributeFilter: ['placeholder', 'title', 'aria-label'],
    });
  }
  globalThis.__antigravityZhCN = {version: '2.15.1', translate};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
