r.f2p.utils = {
    vowels: /a|i|e|o|u/ig,

    tupEach: function(list, iterator, context) {
        if (list == null) {
            return
        }

        if (!_.isArray(list)) {
            list = [list]
        }
        _.each(list, iterator, context)
    },

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
