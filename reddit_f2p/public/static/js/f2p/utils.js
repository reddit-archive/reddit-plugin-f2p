r.f2p.utils = {
    vowels: /a|i|e|o|u/ig,

    textNodes: function(el) {
        return $(el)
            .find('*')
            .andSelf()
            .contents()
            .filter(function() {
                return this.nodeType == 3  // Node.TEXT_NODE
            })
    },

    replaceText: function(el, modifier) {
        r.f2p.utils.textNodes(el).each(function(idx, textEl) {
            var $textEl = $(textEl)
            $textEl.replaceWith(
                modifier($textEl.text())
            )
        })
    }
}
