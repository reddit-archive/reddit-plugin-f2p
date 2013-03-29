r.f2p.utils = {
    vowels: /a|i|e|o|u/ig,

    modifyText: function(el, modifier) {
        $(el)
            .find('*')
            .contents()
            .filter(function() {
                return this.nodeType == Node.TEXT_NODE
            })
            .each(modifier)
    },

    replaceText: function(el, modifier) {
        r.f2p.utils.modifyText(el, function(idx, textEl) {
            textEl.nodeValue = modifier(textEl.nodeValue)
        })
    }
}
