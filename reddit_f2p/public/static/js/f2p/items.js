r.f2p.Item = Backbone.Model.extend({
    defaults: {
        "cursor": "crosshair",
        "description": "lorem ipsum dolor sit amet your hampster",
        "flavor": "flavor flavor flavor flavor flavour flavour flavour flavour flavour"
    }
})

r.f2p.Inventory = Backbone.Collection.extend({
    url: '#inventory',
    model: function(attrs, options) {
        var itemKind = r.f2p.Item.kinds[attrs.kind] || r.f2p.Item
        return new itemKind(attrs, options)
    },

    use: function(item, targetId) {
        $.ajax({
            type: 'post',
            url: '/api/f2p/use_item',
            data: {
                item: item.get('kind'),
                target: targetId
            },
            success: _.bind(function() {
                this.remove(item)
            }, this)
        })
    }
})

r.f2p.Item.kinds = {}

r.f2p.Item.kinds.cdgl = r.f2p.Item.extend({}, {
    applyEffect: function($el) {
        $el.find('.usertext-body .md *').contents()
            .filter(function() {
                return this.nodeType == Node.TEXT_NODE
            })
            .each(function(idx, textEl) {
                textEl.nodeValue = textEl.nodeValue.replace(/a|i|e|o|u/ig, '')
            })
    }
})

r.f2p.Item.kinds.chirality = r.f2p.Item.extend({}, {
    applyEffect: function($el) {
        $el.find('.usertext-body .md').css('text-align', 'right')
    }
})

r.f2p.Item.kinds.cruise = r.f2p.Item.extend({}, {
    applyEffect: function($el) {
        $el.find('.usertext-body .md').html('<p>Tom Cruise</p>')
    }
})

r.f2p.Item.kinds.palindrome = r.f2p.Item.extend({}, {
    applyEffect: function($el) {
        $el.find('.tagline .author').text(
            $el.find('.tagline .author').text().split('').reverse().join('')
        )
    }
})
