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

        this.scorePanel = new r.f2p.Panel({
            id: 'score-panel',
            title: 'scoreboard',
            content: new r.f2p.ScoreView()
        })

        $('body').append(
            this.inventoryPanel.render().el,
            this.scorePanel.render().el
        )
    }
}

r.f2p.Inventory = Backbone.Collection.extend({
    fetch: function() {
        this.add([
            {id: 'cruise', title: 'Cruise Missile'},
            {id: 'downtime_banana', title: 'Banana of Downtime'},
            {id: 'smpl_cdgl', title: 'Smpl Cdgl'},
            {id: 'caltrops', title: 'Spiny Caltrops of the Spineless'}
        ])
    }
})

r.f2p.Panel = Backbone.View.extend({
    events: {
        'click .title-bar': 'minimize'
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
            this.$el.append(r.templates.make('f2p/item', item.toJSON()))
        }, this)
        return this
    }
})

r.f2p.ScoreView = Backbone.View.extend({
    className: 'score-view'
})

$(function() {
   r.f2p.init()
})
