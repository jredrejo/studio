<template>

  <VAutocomplete
    v-model="language"
    class="language-dropdown"
    box
    v-bind="$attrs"
    :items="languages"
    :label="$tr('labelText')"
    color="primary"
    itemValue="id"
    :itemText="languageText"
    autoSelectFirst
    :allowOverflow="false"
    clearable
    :rules="rules"
    :required="required"
    :no-data-text="$tr('noDataText')"
    :search-input.sync="input"
    :menu-props="menuProps"
    :multiple="multiple"
    :chips="multiple"
    @change="input=''"
  >
    <template #item="{item}">
      <VTooltip bottom>
        <template v-slot:activator="{ on }">
          <span class="text-truncate" v-on="on">{{ languageText(item) }}</span>
        </template>
        <span>{{ languageText(item) }}</span>
      </VTooltip>

    </template>
  </VAutocomplete>

</template>


<script>

  import Languages, { LanguagesList } from 'shared/leUtils/Languages';

  export default {
    name: 'LanguageDropdown',
    props: {
      value: {
        type: [String, Array],
        required: false,
        validator: function(value) {
          if (typeof value === 'string') {
            return !value || Languages.has(value);
          }
          return value.every(l => Languages.has(l));
        },
      },
      required: {
        type: Boolean,
        default: false,
      },
      excludeLanguages: {
        type: Array,
        default() {
          return [];
        },
      },
      multiple: {
        type: Boolean,
        default: false,
      },
    },
    data() {
      return {
        input: '',
      };
    },
    computed: {
      language: {
        get() {
          return this.value;
        },
        set(value) {
          this.$emit('input', value);
        },
      },
      menuProps() {
        return {
          minWidth: 300,
          maxWidth: 300,
        };
      },
      languages() {
        const excludeLanguages = new Set(this.excludeLanguages);
        return LanguagesList.filter(l => !excludeLanguages.has(l.id));
      },
      rules() {
        return this.required ? [v => Boolean(v) || this.$tr('languageRequired')] : [];
      },
    },
    methods: {
      languageText(item) {
        return this.$tr('languageItemText', { language: item.native_name, code: item.id });
      },
    },
    $trs: {
      labelText: 'Language',
      languageItemText: '{language} ({code})',
      languageRequired: 'Language is required',
      noDataText: 'No languages found',
    },
  };

</script>


<style lang="less" scoped>

  .language-dropdown {
    display: inline-block;
    width: 100%;
  }

  /deep/ .v-select__selections {
    width: calc(100% - 48px);
    min-height: 0 !important;
  }
  .v-chip,
  /deep/ .v-chip__content,
  .text-truncate {
    max-width: 100%;
  }

</style>