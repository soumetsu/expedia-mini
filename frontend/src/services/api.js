const HOTEL_SEARCH_PATH = '/api/hotels/search'

export class ApiRequestError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
  }
}

export async function searchHotels(name) {
  const parameters = new URLSearchParams({ name })
  let response

  try {
    response = await fetch(`${HOTEL_SEARCH_PATH}?${parameters.toString()}`, {
      headers: { Accept: 'application/json' },
    })
  } catch {
    throw new ApiRequestError('The search service could not be reached.')
  }

  if (!response.ok) {
    throw new ApiRequestError('The search service returned an error.', response.status)
  }

  let data

  try {
    data = await response.json()
  } catch {
    throw new ApiRequestError('The search service returned an invalid response.', response.status)
  }

  if (!data || !Array.isArray(data.results) || !Number.isInteger(data.count)) {
    throw new ApiRequestError('The search service returned an unexpected response.', response.status)
  }

  return data
}
