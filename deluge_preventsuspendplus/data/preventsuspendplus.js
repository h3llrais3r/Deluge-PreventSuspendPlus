/**
 * preventsuspendplus.js
 *      The client-side javascript code for the PreventSuspendPlus plugin.
 *
 * Copyright (C) 2015 h3llrais3r <h3llrais3r.github@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.ns('Deluge.ux.preferences');

Deluge.ux.preferences.PreventSuspendPlusPage = Ext.extend(Ext.Panel, {
    title: _('PreventSuspendPlus'),
    layout: 'fit',
    border: false,

    initComponent: function () {
        Deluge.ux.preferences.PreventSuspendPlusPage.superclass.initComponent.call(this);

        this.form = this.add({
            xtype: 'form',
            layout: 'form',
            border: false,
            autoHeight: true
        });

        this.fieldset = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: 'Settings',
            autoHeight: true,
            labelWidth: 80,
            defaultType: 'checkbox'
        });

        this.chk_enabled = this.fieldset.add({
            xtype: 'checkbox',
            name: 'chk_enabled',
            height: 22,
            hideLabel: true,
            boxLabel: _('Enable suspend prevention')
        });

        this.combo_prevent_when = this.fieldset.add({
            xtype: 'combo',
            name: 'combo_prevent_when',
            width: 200,
            fieldLabel: _('Prevent when'),
            store: new Ext.data.ArrayStore({
                fields: ['id', 'text'],
                data: [
                    [0, _('Downloading')],
                    [1, _('Downloading or seeding')],
                    [2, _('Always')]
                ]
            }),
            mode: 'local',
            editable: false,
            triggerAction: 'all',
            valueField: 'id',
            displayField: 'text'
        });

        deluge.preferences.on('show', this.updateConfig, this);
    },

    onRender: function (ct, position) {
        Deluge.ux.preferences.PreventSuspendPlusPage.superclass.onRender.call(this, ct, position);
        this.form.layout = new Ext.layout.FormLayout();
        this.form.layout.setContainer(this);
        this.form.doLayout();
    },

    onApply: function () {
        // build settings object
        var config = {}

        config['enabled'] = this.chk_enabled.getValue();
        config['prevent_when'] = this.combo_prevent_when.getValue();

        deluge.client.preventsuspendplus.set_config(config);
    },

    onOk: function () {
        this.onApply();
    },

    afterRender: function () {
        Deluge.ux.preferences.PreventSuspendPlusPage.superclass.afterRender.call(this);
        this.updateConfig();
    },

    updateConfig: function () {
        deluge.client.preventsuspendplus.get_config({
            success: function (config) {
                this.chk_enabled.setValue(config['enabled']);
                this.combo_prevent_when.setValue(config['prevent_when']);
            },
            scope: this
        });
    }
});

Deluge.plugins.PreventSuspendPlugin = Ext.extend(Deluge.Plugin, {
    name: 'PreventSuspendPlus',
    prefsPage: null,

    onDisable: function () {
        deluge.preferences.removePage(this.prefsPage);
        this.prefsPage = null;
    },

    onEnable: function () {
        this.prefsPage = deluge.preferences.addPage(new Deluge.ux.preferences.PreventSuspendPlusPage());
    }
});
Deluge.registerPlugin('PreventSuspendPlus', Deluge.plugins.PreventSuspendPlugin);
