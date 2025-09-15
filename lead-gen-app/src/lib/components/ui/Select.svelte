<script lang="ts">
  export let value: string | number = 20;
  export let options: Array<{ label: string; value: string | number }> = [
    { label: '10', value: 10 },
    { label: '20', value: 20 }
  ];
  export let disabled = false;
  export let name = '';
  export let id = '';

  $: classes = 'flex h-10 min-w-40 items-center justify-between border-2 border-foreground bg-background px-4 py-2 text-sm text-foreground placeholder:text-foreground/70 outline-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-md rounded-none';
</script>

<select
  {name}
  {id}
  bind:value
  {disabled}
  class={classes}
  {...$$restProps}
>
  {#each options as opt}
    <option value={opt.value}>{opt.label}</option>
  {/each}
</select>


