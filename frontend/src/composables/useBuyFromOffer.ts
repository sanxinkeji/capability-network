import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { buyFromOffer } from '@/api/buyFromOffer'
import { payDeal } from '@/api/deals'

export function useBuyFromOffer() {
  const router = useRouter()
  const buying = ref(false)
  const error = ref('')

  async function purchaseAndPay(offerId: string, buyerNote?: string) {
    buying.value = true
    error.value = ''
    try {
      const result = await buyFromOffer(offerId, buyerNote)
      try {
        await payDeal(result.deal.id)
        await router.push(`/app/deals/${result.deal.id}/chat`)
      } catch {
        await router.push({ path: `/app/deals/${result.deal.id}`, query: { pay_pending: '1' } })
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '购买失败'
      throw e
    } finally {
      buying.value = false
    }
  }

  return { buying, error, purchaseAndPay }
}
