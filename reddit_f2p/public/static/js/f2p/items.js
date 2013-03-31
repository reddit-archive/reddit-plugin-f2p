r.f2p.targetTypes = {
    'account': 'users',
    'usertext': 'comments and self-posts',
    'link': 'links'
}

r.f2p.Inventory = Backbone.Collection.extend({
    url: '#inventory',
    model: function(attrs, options) {
        var itemKind = r.f2p.Item.kinds[attrs.kind] || r.f2p.Item
        return new itemKind(attrs, options)
    },

    consume: function(kinds) {
        r.f2p.utils.tupEach(kinds, function(kind) {
            var item = this.findWhere({kind: kind})
            if (item) {
                this.remove(item)
            }
        }, this)
    },

    use: function(item, targetId) {
        $.ajax({
            type: 'post',
            url: '/api/f2p/use_item',
            data: {
                item: item.get('kind'),
                target: targetId
            },
            dataType: 'json',
            success: r.f2p.updateState
        })
    }
})

r.f2p.Item = Backbone.Model.extend({
    parse: function(response, options) {
        attributes = Backbone.Model.prototype.parse.apply(this, [response, options])
        attributes['use_on'] = _.map(attributes['targets'], function (t) { return r.f2p.targetTypes[t] || t })
        return attributes
    },

    applyPlayerEffect: function() {},
    unapplyPlayerEffect: function() {}
}, {
    getKind: function(kind) {
        if (/_hat$/.test(kind)) {
            kind = 'hat'
        }
        return r.f2p.Item.kinds[kind] || r.f2p.Item
    },

    applyThingEffect: function() {}
})

r.f2p.Item.kinds = {
    abstinence: r.f2p.Item.extend({
        applyPlayerEffect: function($el) {
            $(document).on('mouseover', '.arrow', $.proxy(this, 'interceptVote'))
        },

        unapplyPlayerEffect: function($el) {
            $(document).off('mouseover', '.arrow', $.proxy(this, 'interceptVote'))
        },

        interceptVote: function(ev) {
            var $target = $(ev.target)
            $target.prop('onclick', null)
            $target.animate({opacity: 0}, function() {
                $target.css('visibility', 'hidden')
            })
        }
    }),

    antigravity: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.replace(/(\w+k\w+|\w+u\w+)/ig, function(match) {
                    return '<sup>' + match.split('').join('<sup>') + Array(match.length + 1).join('</sup>')
                })
            })
        }
    }),

    cdgl: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.replace(r.f2p.utils.vowels, '')
            })
        }
    }),

    chirality: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el.find('.entry:first').addClass('effect-chirality')
        }
    }),

    compensation: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el.find('.entry:first').addClass('effect-compensation')
        }
    }),

    cruise: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            var $md = $el.find('.usertext-body .md:first'),
                $cruise = $('<p>Tom Cruise</p>')

            $cruise.attr('title', $.trim($md.text()))
            $md.empty().append($cruise)
        }
    }),

    discombobulation: r.f2p.Item.extend({
        probability: .1,

        applyPlayerEffect: function($el) {
            $(document).on('mousedown', $.proxy(this, 'interceptClick'))
        },

        unapplyPlayerEffect: function($el) {
            $(document).off('mousedown', $.proxy(this, 'interceptClick'))
        },

        interceptClick: function(ev) {
            // only consider left clicks
            if (ev.which == 1 && Math.random() < this.probability) {
                if (confirm('Are you sure?')) {
                    var $target = $(ev.target)
                    if ($target.attr('href')) {
                        window.location = $target.attr('href')
                    }
                    $target.click()
                }
            }
        }
    }),

    emphasis: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.replace(/(\w+b\w+|\w+e\w+|\w+i\w+)/ig, function(match, group, offset) {
                    if (offset % 2 == 0) {
                        return '<strong>' + match + '</strong>'
                    } else {
                        return '<em>' + match + '</em>'
                    }
                })
            })
        }
    }),

    english: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
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

    hat: r.f2p.Item.extend({}, {
        applyThingEffect: function($authorEl, kind) {
            r.f2p.HatPile.getPile($authorEl).addHat(kind)
        }
    }),

    hatchet: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el.find('.entry:first').addClass('effect-flattened')
        }
    }),

    inebriation: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text
                    .replace(/\bs/ig, 'sh')
                    .replace(/\w+g\w+/ig, '&ndash; *hic* &ndash;')
            })
        }
    }),

    intolerance: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
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

    inversion: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el.find('.entry:first').addClass('effect-inversion')
        }
    }),

    knuckles: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
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

    medal: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el
                .find('.md:first')
                .append('<p>Excelsior!</p>')
        }
    }),

    nostalgia: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                swaps = {
                    'N': '&Ntilde;',
                    'O': '&Ograve;',
                    'a': '&acirc;',
                    'e': '&eacute;',
                    'i': '&iuml;',
                    'o': '&oslash;',
                    'u': '&ugrave;',
                    'c': '&ccedil;',
                    'n': '&ntilde;',
                    's': '&scaron;',
                    'y': '&yacute;',
                    'x': '&times;'
                },
                swapRe = new RegExp(_.keys(swaps).join('|'), 'g')

                return text.replace(swapRe, function(match) {
                    return swaps[match]
                })
            })
        }
    }),

    palindrome: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            var $author = $el.find('.tagline .author:first')
            $author.text(
                $author.text().split('').reverse().join('')
            )
        }
    }),

    patriotism: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.replace(/(\w+w\w+|\w+a\w+|\w+s\w+)/ig, '<span class="effect-redacted">$1</span>')
            })
        }
    }),

    rampart: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el
                .find('.md:first')
                .append('<p>And please be sure to check out Rampart.</p>')
        }
    }),

    scrambler: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.midcol:first .score'), function(text) {
                var digits = text.split(''),
                    newDigits = []

                _.times(digits.length, function() {
                    var idx = _.random(digits.length - 1)
                    newDigits.push(digits[idx])
                    digits.splice(idx, 1)
                })

                return newDigits.join('')
            })
        }
    }),

    shrouding: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            $el.find('.entry:first').addClass('effect-shrouded')
        }
    }),

    shuffler: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            r.f2p.utils.replaceText($el.find('.usertext-body .md:first'), function(text) {
                return text.replace(/[A-Za-z0-9]/g, function(chr) {
                    orig = chr.charCodeAt(0)
                    base = orig > 57 ? (orig > 90 ? 97 : 65) : 48
                    rot = orig + 13 - base
                    offset = rot % (orig > 57 ? 26 : 10)
                    return String.fromCharCode(base + offset)
                })
            })
        }
    }),

    torpor: r.f2p.Item.extend({}, {
        applyThingEffect: function($el) {
            var textNodes = r.f2p.utils.textNodes($el.find('.md:first'))
            if (!textNodes.length) {
                return
            }

            var textNode = textNodes[_.random(textNodes.length - 1)]
            r.f2p.utils.replaceTextNode(textNode, function(text) {
                var sentences = text.split('.'),
                    ts = Date.parse($el.find('.tagline time').attr('datetime')),
                    idx = (text.length + ts / 1000) % sentences.length

                sentences[idx] = sentences[idx] + '&hellip; and then I took an arrow to the knee'
                return sentences.join('.')
            })
        }
    })
}

r.f2p.Effects = Backbone.Model.extend({
    url: '#effects',

    _touch: function(targetId) {
        if (!this.has(targetId)) {
            this.set(targetId, [])
        }
        return this.get(targetId)
    },

    add: function(targetId, kinds) {
        var effects = this._touch(targetId)
        r.f2p.utils.tupEach(kinds, function(kind) {
            effects.push(kind)
            this.trigger('add', targetId, kind)
        }, this)
    },

    remove: function(targetId, kinds) {
        var effects = this._touch(targetId)
        r.f2p.utils.tupEach(kinds, function(kind) {
            var idx = _.indexOf(effects, kind)
            if (idx != -1) {
                effects.splice(idx, 1)
            }
            this.trigger('remove', targetId, kind)
        }, this)
    }
})

r.f2p.EffectUpdater = r.ScrollUpdater.extend({
    // todo: effect removals. save html in data
    selector: '.thing, .noncollapsed .tagline .author',

    initialize: function() {
        this.model.on('add', this.apply, this)
        this.model.on('remove', this.applyAll, this)
    },

    _target: function(target) {
        if (_.isString(target)) {
            return $('[data-fullname="' + target + '"]')
        } else {
            return $(target)
        }
    },

    apply: function(target, kinds) {
        r.f2p.utils.tupEach(kinds, function(kind) {
            var $els = this._target(target),
                itemKind = r.f2p.Item.getKind(kind)

            _.each($els, function(el) {
                itemKind.applyThingEffect($(el), kind)
            })
        }, this)
    },

    reset: function(el) {
        var $el = $(el),
            oldHTML = $el.data('_pre_effects')
        if (oldHTML) {
            $el.html(oldHTML)
        } else {
            $el.data('_pre_effects', $el.html())
        }
    },

    applyAll: function(target, fullname) {
        var $els = this._target(target)
        _.each($els, _.bind(this.reset, this))
        fullname = fullname || $els.data('fullname')
        this.apply($els, this.model.get(fullname))
    },

    start: function() {
        r.ScrollUpdater.prototype.start.apply(this)

        $(document).on('expando_thing', _.bind(function(ev, thing) {
            this.applyAll($(thing).find('.expando'), $(thing).data('fullname'))
        }, this))

        $(document).on('new_thing', _.bind(function(ev, thing) {
            this.update($(thing))
            this.update($(thing).find('.noncollapsed .tagline .author:first'))
        }, this))
    },

    update: function($el) {
        if ($el.data('_updated')) {
            return
        }
        $el.data('_updated', true)
        this.applyAll($el)
    }
})

r.f2p.HatPile = Backbone.View.extend({
    tagName: 'span',
    className: 'hats',

    dims: {
        width: 22,
        height: 13
    },

    initialize: function() {
        this.hats = []
        this.render = _.debounce(this.render, 0)
    },

    addHat: function(kind) {
        this.hats.push(kind)
        this.render()
    },

    render: function() {
        var $author = $(this.options.authorEl),
            $thingEl = $author.closest('.thing'),
            width = $author.width(),
            columnCount = Math.max(1, Math.floor(width / this.dims.width))

        this.$el.empty()

        var cols = []
        _.times(columnCount, function(idx) {
            var $col = $('<span class="stack">')
                .css('left', idx * this.dims.width)
            cols.push($col)
        }, this)

        var curCol = 0
        _.each(this.hats, function(kind, idx) {
            var hat = $('<img class="hat">')
                .attr('src', '/static/images/hat/' + kind + '.png')
                .css('z-index', 100 + idx)
            cols[curCol].prepend(hat)
            curCol = (curCol + 1) % columnCount
        }, this)

        this.$el.append.apply(this.$el, cols)

        $thingEl.css('padding-top', cols[0].children().length * this.dims.height)
        $author.before(this.$el)

        return this
    }
}, {
    getPile: function($el) {
        var existing = $el.data('HatPile')
        if (existing) {
            return existing
        } else {
            var pile = new r.f2p.HatPile({
                authorEl: $el
            })
            $el.data('HatPile', pile)
            return pile
        }
    }
})

r.f2p.PlayerEffects = r.f2p.Inventory.extend({
    url: '#myeffects',

    initialize: function() {
        this.on('add', this.applyEffect, this)
        this.on('remove', this.unapplyEffect, this)
    },

    applyEffect: function(item) {
        item.applyPlayerEffect()
    },

    unapplyEffect: function(item) {
        item.unapplyPlayerEffect()
    }
})
