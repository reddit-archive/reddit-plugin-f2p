r.f2p = {
    init: function() {
        this.inventoryPanel = new r.f2p.Panel({
            id: 'inventory-panel',
            title: 'inventory',
            content: new r.f2p.InventoryView()
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
        return this
    },

    minimize: function() {
        this.minimized = !this.minimized

        this.$el.toggleClass('minimized', this.minimized)

        var props = {}
        if (this.minimized) {
            props = {height: 0}
        } else {
            props = {height: this.options.content.$el.height()}
        }

        this.$('.panel-content').animate(props, 250)
    }
})

r.f2p.InventoryView = Backbone.View.extend({
    className: 'inventory-view'
})

r.f2p.ScoreView = Backbone.View.extend({
    className: 'score-view'
})

$(function() {
   r.f2p.init()
})
