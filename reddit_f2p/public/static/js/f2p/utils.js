r.f2p.utils = {
    vowels: /a|i|e|o|u/ig,

    modifyText: function(el, modifier) {
        $(el)
            .find('.usertext-body .md *')
            .contents()
            .filter(function() {
                return this.nodeType == Node.TEXT_NODE
            })
            .each(modifier)
    }
}
