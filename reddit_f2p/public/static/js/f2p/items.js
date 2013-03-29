r.f2p.Item = Backbone.Model.extend({})

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
                r.f2p.pageEffects.applyItem(item, targetId)
            }, this)
        })
    }
})

r.f2p.Item.kinds = {
    cdgl: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.modifyText($el.find('.usertext-body .md:first'),
                function(idx, textEl) {
                    textEl.nodeValue = textEl.nodeValue.replace(r.f2p.utils.vowels, '')
                }
            )
        }
    }),

    chirality: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.usertext-body .md:first').css('text-align', 'right')
        }
    }),

    cruise: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.usertext-body .md:first').html('<p>Tom Cruise</p>')
        }
    }),

    hatchet: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.md:first').addClass('flattened')
        }
    }),

    intolerance: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.modifyText($el.find('.usertext-body .md:first'),
                function(idx, textEl) {
                    textEl.nodeValue = textEl.nodeValue.toUpperCase().replace(/[.,]/g, function() {
                        tail = []
                        for (var i = 0; i < _.random(10); i++) {
                            tail.push('!')
                        }
                        for (var i = 0; i < _.random(5); i++) {
                            tail.push('1')
                        }
                        return tail.join('')
                    })
                }
            )
        }
    }),

    knuckles: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.modifyText($el.find('.usertext-body .md:first'),
                function(idx, textEl) {
                    var text = textEl.nodeValue,
                        vowels = text.match(r.f2p.utils.vowels)

                    if (!vowels) {
                        return
                    }

                    vowels.push(vowels.shift())
                    textEl.nodeValue = text.replace(r.f2p.utils.vowels, function() {
                        return vowels.shift()
                    })
                }
            )
        }
    }),

    palindrome: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            var $author = $el.find('.tagline .author:first')
            $author.text(
                $author.text().split('').reverse().join('')
            )
        }
    }),

    patriotism: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.modifyText($el.find('.usertext-body .md:first'),
                function(idx, textEl) {
                    var $parent = $(textEl).parent()
                    $parent.html(
                        $parent.text().replace(/(\w+w\w+|\w+a\w+|\w+s\w+)/ig, '<span class="redacted">$1</span>')
                    )
                }
            )
        }
    }),

    shrouding: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.md:first').addClass('shrouded')
        }
    })
}

