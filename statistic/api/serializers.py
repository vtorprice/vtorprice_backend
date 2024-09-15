from common.serializers import NonNullDynamicFieldsModelSerializer
from exchange.api.serializers import ExchangeRecyclablesSerializer
from exchange.models import RecyclablesDeal, DealStatus, RecyclablesApplication
from product.models import Recyclables


class RecyclablesStatisticsSerializer(ExchangeRecyclablesSerializer):
    def get_deviation_percent(self, instance: Recyclables):
        lower_date_bound = self.context.get("lower_date_bound")
        additional_filters = {}

        if lower_date_bound:
            additional_filters[
                "application__created_at__gte"
            ] = lower_date_bound

        # FIXME: Попробовать сделать через аннотации в get_queryset
        try:
            latest_deal = RecyclablesDeal.objects.filter(
                application__recyclables=instance,
                status=DealStatus.COMPLETED,
                **additional_filters,
            ).latest("created_at")
        except RecyclablesDeal.DoesNotExist:
            latest_deal = None

        if not latest_deal:
            return None

        try:
            first_deal = (
                RecyclablesDeal.objects.filter(
                    application__recyclables=instance,
                    status=DealStatus.COMPLETED,
                    **additional_filters,
                )
                .exclude(pk=latest_deal.pk)
                .earliest("created_at")
            )
        except RecyclablesDeal.DoesNotExist:
            first_deal = None

        if not first_deal:
            return None

        latest_deal_price = float(latest_deal.price)
        pre_latest_deal_price = float(first_deal.price)
        return round(
            (latest_deal_price - pre_latest_deal_price)
            / pre_latest_deal_price
            * 100,
            2,
        )

    def get_deviation(self, instance: Recyclables):
        deviation_percent = self.get_deviation_percent(instance)
        if not deviation_percent or deviation_percent == 0:
            return 0
        if deviation_percent > 0:
            return 1
        return -1


class RecyclablesApplicationStatisticsSerializer(
    NonNullDynamicFieldsModelSerializer
):
    recyclables = ExchangeRecyclablesSerializer

    class Meta:
        model = RecyclablesApplication
