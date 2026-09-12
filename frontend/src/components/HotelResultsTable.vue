<script setup>
defineProps({
  results: {
    type: Array,
    required: true,
  },
})

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatUsd(value) {
  return usdFormatter.format(Number(value))
}
</script>

<template>
  <section class="results" aria-labelledby="results-title">
    <h2 id="results-title">Available stays</h2>

    <div class="table-scroll" tabindex="0" aria-label="Available hotel stays table">
      <table>
        <thead>
          <tr>
            <th scope="col">Hotel</th>
            <th scope="col">Location</th>
            <th scope="col">Stay ID</th>
            <th scope="col">Stay</th>
            <th scope="col">Check-in</th>
            <th scope="col">Check-out</th>
            <th scope="col">Nights</th>
            <th scope="col">Nightly rate</th>
            <th scope="col">Estimated price</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stay in results" :key="stay.trip_id">
            <td>{{ stay.hotel_name }}</td>
            <td>{{ stay.city }}, {{ stay.state }}</td>
            <td>{{ stay.trip_id }}</td>
            <td>{{ stay.trip_name }}</td>
            <td>{{ stay.check_in }}</td>
            <td>{{ stay.check_out }}</td>
            <td>{{ stay.nights }}</td>
            <td>{{ formatUsd(stay.nightly_rate_usd) }}</td>
            <td>{{ formatUsd(stay.estimated_stay_price_usd) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
