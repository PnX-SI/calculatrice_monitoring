import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatListOption } from '@angular/material/list';
import { ActivatedRoute, Router } from '@angular/router';
import {
  Campaign,
  Indicator,
  parseCampaigns,
  Protocol,
  serializeCampaigns,
  Site,
  SitesGroup,
  VisualizationBlockDefinition,
  VisualizationError,
} from '../../interfaces';
import { DataService } from '../../services/data.service';
import { PermissionService } from '../../services/permission.service';

interface Selection {
  label: string;
  type: 'overview' | 'campaign' | 'statisticalTests';
  campaigns: Campaign[];
  disabled?: boolean;
  tooltip?: string;
}

@Component({
  selector: 'pnx-calc-visualization-page',
  templateUrl: './visualization-page.component.html',
  styleUrls: ['./visualization-page.component.css'],
})
export class VisualizationPageComponent implements OnInit {
  protected vizBlocks: VisualizationBlockDefinition[];
  protected visualizationError?: VisualizationError;
  protected selections: Selection[];
  protected currentSelection?: Selection;
  protected availableCampaigns: Campaign[] = [];
  protected firstSelectedCampaign?: Campaign;
  protected secondSelectedCampaign?: Campaign;
  protected firstCampaignControl = new FormControl('');
  protected secondCampaignControl = new FormControl('');
  protected indicatorId: number;
  protected queryParams: { sitesGroup?: number; campaigns?: string } = {};
  private _sites: Site[];
  private _campaigns: Campaign[];
  private _indicatorId: number;

  constructor(
    private _data: DataService,
    private _router: Router,
    private _route: ActivatedRoute,
    private _permissionService: PermissionService
  ) {}

  ngOnInit() {
    this._route.params.subscribe((params) => {
      this.indicatorId = Number(params.indicatorId);
      this._indicatorId = this.indicatorId;

      const queryParams = this._route.snapshot.queryParams;
      let sitesGroupId = queryParams['sitesGroup'] ? Number(queryParams['sitesGroup']) : undefined;
      let campaignsParam = queryParams['campaigns']
        ? parseCampaigns(queryParams['campaigns'])
        : undefined;

      const cachedParams = sessionStorage.getItem(`calc-viz-params:${this._indicatorId}`);
      const parsed = cachedParams ? JSON.parse(cachedParams) : undefined;

      if (!sitesGroupId && parsed?.sitesGroupId) {
        sitesGroupId = Number(parsed.sitesGroupId);
      }
      if ((!campaignsParam || campaignsParam.length === 0) && parsed?.campaigns) {
        campaignsParam = parsed.campaigns;
      }

      this._campaigns = campaignsParam;
      this._sites = parsed?.sites;

      this.queryParams = {
        sitesGroup: sitesGroupId,
        campaigns: campaignsParam ? serializeCampaigns(campaignsParam) : undefined,
      };

      if (!this._campaigns || this._campaigns.length === 0) {
        this._router.navigate(['./params'], {
          relativeTo: this._route,
          queryParams: this.queryParams,
        });
        return;
      }

      if (this._sites) {
        this._renderVisualization();
      } else if (sitesGroupId) {
        this._data.getIndicator(this._indicatorId).subscribe((indicator: Indicator) => {
          this._data.getProtocol(indicator.protocolId).subscribe((protocol: Protocol) => {
            this._data
              .getSites(protocol.code, { id: sitesGroupId } as SitesGroup)
              .subscribe((sites) => {
                this._sites = sites;
                sessionStorage.setItem(
                  `calc-viz-params:${this._indicatorId}`,
                  JSON.stringify({
                    sites,
                    campaigns: this._campaigns,
                    sitesGroupId,
                  })
                );
                this._renderVisualization();
              });
          });
        });
      } else {
        this._router.navigate(['./params'], {
          relativeTo: this._route,
          queryParams: this.queryParams,
        });
      }
    });
  }

  private _renderVisualization() {
    this.availableCampaigns = this._campaigns || [];
    if (this.availableCampaigns.length >= 2) {
      this.firstSelectedCampaign = this.availableCampaigns[0];
      this.secondSelectedCampaign = this.availableCampaigns[1];
      this.firstCampaignControl.setValue(this.getCampaignKey(this.firstSelectedCampaign), {
        emitEvent: false,
      });
      this.secondCampaignControl.setValue(this.getCampaignKey(this.secondSelectedCampaign), {
        emitEvent: false,
      });
    }
    this.selections = this._buildSelections(this.availableCampaigns);
    const firstSelectableSelection = this.selections.find((selection) => !selection.disabled);
    if (firstSelectableSelection) {
      this.currentSelection = firstSelectableSelection;
      if (firstSelectableSelection.type === 'statisticalTests') {
        this._updateStatisticalTestsVisualization();
      } else {
        this._updateVisualization(firstSelectableSelection);
      }
    }
  }

  onSelectionsChange(selectedOptions: MatListOption[]) {
    // The selection list is configured to allow single item selection only.
    const selectedOption = selectedOptions[0];
    if (!selectedOption) {
      return;
    }
    const selection: Selection = selectedOption.value;
    if (selection.disabled) {
      return;
    }
    this.currentSelection = selection;
    if (selection.type === 'statisticalTests') {
      this._updateStatisticalTestsVisualization();
    } else {
      this._updateVisualization(selection);
    }
  }

  private _buildSelections(campaigns: Campaign[]): Selection[] {
    const selections: Selection[] = [];
    if (campaigns.length > 1) {
      selections.push({
        label: 'Synthèse',
        type: 'overview',
        campaigns: campaigns,
      });
    } else {
      selections.push({
        label: 'Synthèse',
        type: 'overview',
        campaigns: campaigns,
        disabled: true,
        tooltip: "La synthèse n'est disponible que si plusieurs campagnes sont paramétrées",
      });
    }

    campaigns.forEach((campaign) => {
      selections.push({
        label: `Campagne ${campaign.startDate}-${campaign.endDate}`,
        type: 'campaign',
        campaigns: [campaign],
      });
    });

    if (campaigns.length > 1) {
      const statisticalCampaigns: Campaign[] = [];
      if (this.firstSelectedCampaign && this.secondSelectedCampaign) {
        statisticalCampaigns.push(this.firstSelectedCampaign, this.secondSelectedCampaign);
      }
      selections.push({
        label: 'Tests statistiques',
        type: 'statisticalTests',
        campaigns: statisticalCampaigns,
      });
    } else {
      selections.push({
        label: 'Tests statistiques',
        type: 'statisticalTests',
        campaigns: [],
        disabled: true,
        tooltip:
          'Les tests statistiques ne sont disponibles que si plusieurs campagnes sont paramétrées',
      });
    }

    return selections;
  }

  getCampaignKey(campaign?: Campaign): string {
    return campaign ? `${campaign.startDate}_${campaign.endDate}` : '';
  }

  onCampaignChange() {
    this.firstSelectedCampaign = this.availableCampaigns.find(
      (campaign) => this.getCampaignKey(campaign) === this.firstCampaignControl.value
    );
    this.secondSelectedCampaign = this.availableCampaigns.find(
      (campaign) => this.getCampaignKey(campaign) === this.secondCampaignControl.value
    );
    this._updateStatisticalTestsVisualization();
  }

  private _updateStatisticalTestsVisualization() {
    if (this.firstSelectedCampaign && this.secondSelectedCampaign) {
      this._updateVisualization({
        label: 'Tests statistiques',
        type: 'statisticalTests',
        campaigns: [this.firstSelectedCampaign, this.secondSelectedCampaign],
      });
    }
  }

  private _updateVisualization(vizSelection: Selection) {
    this._data
      .getVisualizationBlocks(
        this._indicatorId,
        this._sites,
        vizSelection.campaigns,
        vizSelection.type
      )
      .subscribe((visualizationData) => {
        this.vizBlocks = visualizationData.vizBlocks;
        this.visualizationError = visualizationData.error;
      });
  }

  isUserAdmin(): boolean {
    // We use update permission because having acess to error
    // is for debugging when updating indicator
    return this._permissionService.getAdminPermission('U') > 0;
  }

  showGenericError() {
    return this.visualizationError?.type === 'internal' && !this.isUserAdmin();
  }
}
