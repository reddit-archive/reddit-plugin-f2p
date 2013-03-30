r.f2p.targetTypes = {
    'account': 'users',
    'usertext': 'comments and self-posts',
    'link': 'links'
}

r.f2p.Item = Backbone.Model.extend({
    parse: function(response, options) {
        attributes = Backbone.Model.prototype.parse.apply(this, [response, options])
        attributes['use_on'] = _.map(attributes['targets'], function (t) { return r.f2p.targetTypes[t] || t })
        return attributes
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
                r.f2p.pageEffects.applyItem(item, targetId)
            }, this)
        })
    }
})

r.f2p.Item.kinds = {
    cdgl: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.replace(r.f2p.utils.vowels, '')
            })
        }
    }),

    chirality: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.usertext-body .md:first').css('text-align', 'right')
        }
    }),

    compensation: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.entry:first').addClass('effect-compensation')
        }
    }),

    cruise: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.usertext-body .md:first').html('<p>Tom Cruise</p>')
        }
    }),

    english: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                var wordSwaps = {
                        'a lot': 'alot',
                        'a': 'an',
                        'an': 'a',
                        'you': 'u',
                        "you're": 'your',
                        'your': "you're",
                        'too': 'to',
                        'to': 'too'
                    },
                    wordSwapRe = new RegExp('\\b' + _.keys(wordSwaps).join('\\b|\\b') + '\\b', 'ig')

                return text
                    .replace(/i/ig, 'i')
                    .replace(/,/ig, '')
                    .replace(wordSwapRe, function(match) {
                        return wordSwaps[match]
                    })
            })
        }
    }),

    hatchet: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.entry:first').addClass('effect-flattened')
        }
    }),

    intolerance: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.toUpperCase().replace(/[.,]/g, function() {
                    tail = []
                    for (var i = 0; i < _.random(10); i++) {
                        tail.push('!')
                    }
                    for (var i = 0; i < _.random(5); i++) {
                        tail.push('1')
                    }
                    return tail.join('')
                })
            })
        }
    }),

    knuckles: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                vowels = text.match(r.f2p.utils.vowels)

                if (!vowels) {
                    return
                }

                vowels.push(vowels.shift())
                return text.replace(r.f2p.utils.vowels, function() {
                    return vowels.shift()
                })
            })
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
                        $parent.text().replace(/(\w+w\w+|\w+a\w+|\w+s\w+)/ig, '<span class="effect-redacted">$1</span>')
                    )
                }
            )
        }
    }),

    rampart: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el
                .find('.md:first')
                .append('<p>And please be sure to check out Rampart.</p>')
        }
    }),

    shrouding: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            $el.find('.entry:first').addClass('effect-shrouded')
        }
    }),

    torpor: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            var textEls = r.f2p.utils.textNodes($el.find('.md:first')),
                textEl = textEls[_.random(textEls.length - 1)],
                sentences = textEl.nodeValue.split('.'),
                ts = Date.parse($el.find('.tagline time').attr('datetime')),
                idx = (textEl.nodeValue.length + ts / 1000) % sentences.length

            sentences[idx] = sentences[idx] + '... and then I took an arrow to the knee'
            textEl.nodeValue = sentences.join('.')
        }
    }),

    shuffler: r.f2p.Item.extend({}, {
        applyEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                 return text.replace(/[A-Za-z0-9]/g, function(chr) {
                    orig = chr.charCodeAt(0)
                    base = orig > 57 ? ( orig > 90 ? 97 : 65 ) : 48
                    rot = orig + 13 - base
                    offset = rot % ( orig > 57 ? 26 : 10 )
                    return String.fromCharCode(base + offset)
                })
            })
        }
    })
}

