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

    replaceText: function(el, modifier) {
        r.f2p.utils.textNodes(el).each(function(idx, textEl) {
            var $parent = $(textEl).parent()
            $parent.html(
                modifier($parent.text())
            )
        })
    }
}
