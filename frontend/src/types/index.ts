export type DashboardSummary = {
  hospitals: number;
  products: number;
  healthy_pct: number;
  critical_risks: number;
  medium_risks: number;
  pending_recommendations: number;
  delayed_shipments: number;
  status_headline: string;
  status_detail: string;
  next_action: string;
};

export type DemoSpotlight = {
  hospital_id: string;
  hospital_name: string;
  product_id: string;
  product_name: string;
  current_stock: number;
  safety_stock: number;
  scheduled_procedures: number;
  procedure_type: string;
  procedure_demand: number;
  shipment_id: string;
  shipment_status: string;
  delay_hours: number;
  expected_delivery?: string;
  supplier_name?: string;
  risk_level: string;
  projected_inventory: number;
  projected_demand: number;
  surplus_hospital_id: string;
  surplus_hospital_name: string;
  surplus_quantity: number;
  story: string;
  pipeline_hint: string;
};

export type Risk = {
  prediction_id?: number;
  hospital_id: string;
  product_id: string;
  product_name?: string;
  hospital_name?: string;
  risk_level: string;
  current_inventory: number;
  projected_demand: number;
  projected_inventory: number;
  predicted_stockout?: string;
  reason?: string;
  created_at?: string;
  plain_english?: string;
};

export type Recommendation = {
  recommendation_id: number;
  source_hospital_id: string;
  target_hospital_id: string;
  source_hospital_name?: string;
  target_hospital_name?: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  reason?: string;
  status: string;
  created_at?: string;
  plain_english?: string;
};

export type EventItem = {
  event_id: number;
  event_type: string;
  hospital_id?: string;
  product_id?: string;
  supplier_id?: string;
  hospital_name?: string;
  product_name?: string;
  message?: string;
  payload?: Record<string, unknown>;
  event_time: string;
};

export type Forecast = {
  hospital_id: string;
  product_id: string;
  window_hours: number;
  forecasted_demand: number;
  baseline_consumption: number;
  procedure_demand: number;
  current_inventory: number;
  safety_stock: number;
  projected_inventory: number;
  series: Array<{
    hour: number;
    time: string;
    inventory: number;
    demand_cumulative: number;
    safety_stock: number;
  }>;
};

export type SimulateResult = {
  shipment_id: string;
  delay_hours: number;
  status: string;
  expected_delivery?: string;
  critical_risks_before: number;
  critical_risks_after: number;
  risks: Risk[];
  recommendations: Recommendation[];
  explanation?: string;
  next_step?: string;
};
