r.f2p.utils = {
    vowels: /a|i|e|o|u/ig,

    textNodes: function(el) {
        return $(el)
            .find('*')
            .contents()
            .filter(function() {
                return this.nodeType == Node.TEXT_NODE
            })
    },

    modifyText: function(el, modifier) {
        r.f2p.utils.textNodes(el).each(modifier)
    },

    replaceText: function(el, modifier) {
        r.f2p.utils.modifyText(el, function(idx, textEl) {
            textEl.nodeValue = modifier(textEl.nodeValue)
        })
    }
}
