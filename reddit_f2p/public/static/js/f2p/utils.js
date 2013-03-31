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
                // Node.TEXT_NODE == 3
                return this.nodeType == 3 && $.trim(this.nodeValue)
            })
    },

    replaceText: function(el, modifier) {
        r.f2p.utils.textNodes(el).each(function(idx, textEl) {
            var $textEl = $(textEl)
            $textEl.replaceWith(
                modifier($('<div>').text(textEl.nodeValue).html())
            )
        })
    }
}
