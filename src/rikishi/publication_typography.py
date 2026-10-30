"""Progressive text-only typography for the static publication reader."""

from typing import Final

SCIENTIFIC_NOTATION_SCRIPT: Final = r"""<script id="rikishi-scientific-numbers">
(() => {
  const normalize = () => {
    const excluded = 'script,style,pre,code,textarea,svg,math,.math,mjx-container,' +
      'a,.rikishi-scientific-number,[contenteditable]:not([contenteditable="false"])';
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: node => node.parentElement && !node.parentElement.closest(excluded)
        ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const text = node.textContent;
      const matches = [...text.matchAll(/(?<![\w.])[+\-−]?(?:\d+(?:\.\d*)?|\.\d+)[eE][+\-−]?\d+(?!\w)/g)]
        .filter(match => match[0].length <= 24);
      if (!matches.length) continue;
      const fragment = document.createDocumentFragment();
      let start = 0;
      for (const match of matches) {
        fragment.append(document.createTextNode(text.slice(start, match.index)));
        const atom = document.createElement('span');
        atom.className = 'rikishi-scientific-number';
        atom.textContent = match[0];
        fragment.append(atom);
        start = match.index + match[0].length;
      }
      fragment.append(document.createTextNode(text.slice(start)));
      node.replaceWith(fragment);
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', normalize, {once:true});
  } else {
    normalize();
  }
})();
</script>"""
