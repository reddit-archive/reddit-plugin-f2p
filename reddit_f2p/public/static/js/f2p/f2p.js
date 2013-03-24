r.f2p = {
    init: function() {
        this.inventory = new r.f2p.Inventory()
        this.inventory.fetch()
        this.inventoryPanel = new r.f2p.Panel({
            id: 'inventory-panel',
            title: 'inventory',
            content: new r.f2p.InventoryView({
                collection: this.inventory,
            })
        })

        this.gameStatus = new r.f2p.GameStatus()
        this.gameStatus.fetch()
        this.scorePanel = new r.f2p.Panel({
            id: 'score-panel',
            title: 'scoreboard',
            content: new r.f2p.ScoreView({
                model: this.gameStatus
            })
        })

        $('body').append(
            this.inventoryPanel.render().el,
            this.scorePanel.render().el
        )

        $('.tagline .author').each(function(idx, el) {
            new r.f2p.HatPile({
                el: el,
                hats: [1, 2, 3, 4, 5, 6, 7, 8, 9]
            }).render()
        })
    }
}

r.f2p.Inventory = Backbone.Collection.extend({
    url: '#inventory'
})

r.f2p.GameStatus = Backbone.Model.extend({
    url: '#game_status'
})

r.f2p.Panel = Backbone.View.extend({
    events: {
        'click .title-bar, .minimize-button': 'minimize'
    },

    initialize: function() {
        this.minimized = false
        this.setElement(r.templates.make('f2p/panel', {
            id: this.id,
            title: this.options.title
        }))
    },

    render: function() {
        this.$('.panel-content').empty().append(
            this.options.content.render().el
        )

        // once content is positioned, set max-height required for css transition.
        _.defer(_.bind(function() {
            this.$('.panel-content').css('max-height', this.options.content.$el.outerHeight())
        }, this))

        return this
    },

    minimize: function() {
        this.minimized = !this.minimized
        this.$el.toggleClass('minimized', this.minimized)
    }
})

r.f2p.InventoryView = Backbone.View.extend({
    className: 'inventory-view',
    tagName: 'ul',

    render: function() {
        this.collection.each(function(item) {
            this.$el.append(
                r.templates.make('f2p/item', item.toJSON())
            )
        }, this)
        return this
    }
})

r.f2p.ScoreView = Backbone.View.extend({
    className: 'score-view',

    render: function() {
        this.$el.html(
            r.templates.make('f2p/scores', this.model.toJSON())
        )
        return this
    }
})

r.f2p.HatPile = Backbone.View.extend({
    dims: {
        width: 20,
        height: 7,
        xJitter: 3,
        yJitter: 1,
        rotJitter: 10
    },

    render: function() {
        var pile = $('<div class="hats">'),
            maxLeft = this.$el.width(),
            curRow = 0,
            curLeft = 0

        _.each(this.options.hats, function() {
            var hat = $('<div class="hat">')

            hat.css({
                position: 'absolute',
                left: curLeft,
                bottom: curRow * this.dims.height + _.random(this.dims.yJitter)
            })

            var rotation = _.random(-this.dims.rotJitter / 2, this.dims.rotJitter / 2),
                transform = 'rotate(' + rotation + 'deg)'
            hat.css({
                '-webkit-transform': transform,
                '-moz-transform': transform,
                '-ms-transform': transform,
                'transform': transform
            })

            pile.append(hat)

            curLeft += this.dims.width + _.random(this.dims.xJitter)
            if (curLeft + this.dims.width > maxLeft) {
                curRow += 1
                curLeft = 0
            }
        }, this)

        var targetPos = this.$el.position()
        pile.css({
            position: 'absolute',
            left: targetPos.left
        })
        this.$el.after(pile)
        return this
    }
})

$(function() {
   r.f2p.init()
})
