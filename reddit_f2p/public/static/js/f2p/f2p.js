r.f2p = {
    init: function() {
        this.myEffects = new r.f2p.PlayerEffects()
        this.inventory = new r.f2p.Inventory()
        this.inventoryPanel = new r.f2p.Panel({
            id: 'items-panel',
            title: 'items',
            content: r.config.logged
                ? [
                    new r.f2p.MyEffectsView({
                        collection: this.myEffects,
                    }),
                    new r.f2p.InventoryView({
                        collection: this.inventory,
                    })
                ]
                : new r.f2p.LoginMessageView()
        })
        $('body').append(this.inventoryPanel.render().el)
        this.inventory.fetch()
        this.myEffects.fetch()

        this.gameStatus = new r.f2p.GameStatus()
        this.scorePanel = new r.f2p.Panel({
            id: 'score-panel',
            title: 'scoreboard',
            content: new r.f2p.ScoreView({
                model: this.gameStatus
            })
        })
        $('body').append(this.scorePanel.render().el)
        this.gameStatus.fetch()

        this.targetOverlay = new r.f2p.TargetOverlay()
        $('body').append(this.targetOverlay.render().el)

        this.pageEffects = new r.f2p.Effects()
        this.pageEffects.fetch()
        this.effectUpdater = new r.f2p.EffectUpdater({
            model: this.pageEffects
        }).start()
    },

    updateState: function(updates) {
        r.debug('updating f2p game state', updates)

        if (updates.status) {
            r.f2p.gameStatus.set(updates.status)
        }

        if (updates.inventory.add) {
            r.f2p.inventory.add(updates.inventory.add)
        }

        if (updates.inventory.consume) {
            r.f2p.inventory.consume(updates.inventory.consume)
        }

        if (updates.effects.add) {
            _.each(updates.effects.add, function(kinds, targetId) {
                r.f2p.pageEffects.add(targetId, kinds)
            })
        }

        if (updates.effects.remove) {
            _.each(updates.effects.remove, function(kinds, targetId) {
                r.f2p.pageEffects.remove(targetId, kinds)
            })
        }

        if (updates.myeffects.add) {
            r.f2p.myEffects.add(updates.myeffects.add)
        }

        if (updates.myeffects.consume) {
            r.f2p.myEffects.consume(updates.myeffects.consume)
        }
    }
}

r.f2p.GameStatus = Backbone.Model.extend({
    url: '#game_status'
})

r.f2p.Panel = Backbone.View.extend({
    events: {
        'click .title-bar, .minimize-button': 'minimize'
    },

    initialize: function() {
        this.setElement(r.templates.make('f2p/panel', {
            id: this.id,
            title: this.options.title
        }))
        this.storeKey = 'f2p.' + this.id + 'minimized'
        this._minimize(store.get(this.storeKey) == true)
    },

    render: function() {
        this.$('.panel-content').empty()
        r.f2p.utils.tupEach(this.options.content, function(contentView) {
            this.$('.panel-content').append(
                contentView.render().el
            )
        }, this)

        // once content is positioned, set max-height required for css transition.
        _.defer(_.bind(function() {
            var height = 0
            r.f2p.utils.tupEach(this.options.content, function(contentView) {
                height += contentView.$el.outerHeight()
            }, this)
            this.$('.panel-content').css('max-height', height)
        }, this))

        return this
    },

    _minimize: function(minimized) {
        store.set(this.storeKey, minimized)
        this.$el.toggleClass('minimized', minimized)
    },

    minimize: function() {
        this._minimize(!this.$el.hasClass('minimized'))
    }
})

r.f2p.LoginMessageView = Backbone.View.extend({
    className: 'login-message',

    render: function() {
        this.$el.html(r.templates.make('f2p/login-message'))
        return this
    },
})

r.f2p.ItemsView = Backbone.View.extend({
    initialize: function() {
        this._itemViews = {}
        this.bubbleGroup = {}
        this.listenTo(this.collection, 'add', this.addOne)
        this.listenTo(this.collection, 'remove', this.removeOne)
        this.listenTo(this.collection, 'reset', this.addAll)
    },

    render: function() {
        this.$el.append('<ul>')
        return this
    },

    addAll: function() {
        this.collection.each(this.addOne, this)
    },

    addOne: function(item) {
        var view = new r.f2p.ItemView({
            model: item,
            bubbleGroup: this.bubbleGroup
        })
        this._itemViews[item.cid] = view
        this.$('ul').append(view.render().el)
    },

    removeOne: function(item) {
        var view = this._itemViews[item.cid]
        if (view) {
            view.remove()
            delete this._itemViews[view.cid]
        }
    }
})

r.f2p.InventoryView = r.f2p.ItemsView.extend({
    className: 'item-view inventory-view'
})

r.f2p.MyEffectsView = r.f2p.ItemsView.extend({
    className: 'item-view myeffects-view',

    initialize: function() {
        r.f2p.ItemsView.prototype.initialize.call(this)
        this.listenTo(this.collection, 'all', this.setVisibility)
    },

    addOne: function(item) {
        if (!/_hat$/.test(item.get('kind'))) {
            r.f2p.ItemsView.prototype.addOne.call(this, item)
        }
    },

    setVisibility: function() {
        this.$el.toggle(!!this.collection.length)
    }
})

r.f2p.ItemView = Backbone.View.extend({
    tagName: 'li',
    className: 'item',

    events: {
        'click': 'activate'
    },

    initialize: function() {
        this.bubble = new r.f2p.ItemBubble({
            model: this.model,
            parent: this.$el,
            group: this.options.bubbleGroup
        })
    },

    render: function() {
        this.$el.html(
            r.templates.make('f2p/item', this.model.toJSON())
        )
        return this
    },

    activate: function() {
        r.f2p.targetOverlay.displayFor(this.model)
    }
})

r.f2p.ItemBubble = r.ui.Bubble.extend({
    className: 'item-bubble hover-bubble anchor-right',

    showDelay: 0,
    hideDelay: 0,

    render: function() {
        this.$el.html(
            r.templates.make('f2p/item-bubble', this.model.toJSON())
        )
        return this
    }
})

r.f2p.TargetOverlay = Backbone.View.extend({
    id: 'f2p-target-overlay',

    events: {
        'click .shade': 'cancel',
        'click .target-cover': 'select',
    },

    targetKinds: {
        'account': {
            selector: '.tagline a.author',
            getId: function(el) {
                return $(el).data('fullname')
            }
        },
        'link': {
            selector: '.thing.link a.title',
            getId: function(el) {
                return $(el).parents('.thing').data('fullname')
            }
        },
        'usertext': {
            selector: '.comment .usertext-body, .link .usertext-body',
            getId: function(el) {
                return $(el).parents('.thing').data('fullname')
            }
        }
    },

    displayFor: function(item) {
        if (this.activeItem != item) {
            this.cancel()
        }

        this.activeItem = item

        var kinds = _.pick(this.targetKinds, item.get('targets')),
            selectors = _.pluck(kinds, 'selector')

        this.$el.html(
            r.templates.make('f2p/target-overlay', {
                selector: _.values(selectors).join(', ')
            })
        )

        $('body').css({
            'cursor': 'url(/static/images/cur/' + item.get('kind') + '.png), auto'
        })

        var container = this.$('.target-overlay')
        container.empty()
        _.each(kinds, function(kind, kindName) {
            $(kind.selector).each(function() {
                var $el = $(this),
                    offset = $el.offset(),
                    targetShape = $('<div>')
                        .css({
                            left: offset.left,
                            top: offset.top,
                            width: $el.width(),
                            height: $el.height()
                        })
                        .addClass('target-' + kindName)

                var targetCover = targetShape.clone()
                    .data('target-id', kind.getId($el))

                targetShape.addClass('target-bg')
                targetCover.addClass('target-cover')

                container.append(targetShape, targetCover)
            })
        }, this)

        $(window).on('keydown.targetOverlay', $.proxy(this, 'keydown'))

        this.$el.show()
    },

    keydown: function(ev) {
        if (ev.which == 27) {
            // ESC
            this.cancel()
        }
    },

    cancel: function() {
        this.$el.hide()
        this.$el.empty()
        this.activeItem = null
        $(window).off('keydown.targetOverlay')
        $('body').css({'cursor': 'auto'})
    },

    select: function(ev) {
        var targetId = $(ev.target).data('target-id')
        r.f2p.inventory.use(this.activeItem, targetId)
        this.cancel()
    }
})

r.f2p.ScoreView = Backbone.View.extend({
    className: 'score-view',

    initialize: function() {
        this.listenTo(this.model, 'change', this.render)
    },

    render: function() {
        this.$el.html(
            r.templates.make('f2p/scores', this.model.toJSON())
        )
        return this
    }
})

$(function() {
   r.f2p.init()
})
