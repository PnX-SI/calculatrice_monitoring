import { Component, OnInit } from '@angular/core';
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
  type: 'synthese' | 'campaign' | 'evolution';
  campaigns: Campaign[];
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
    this.selections = this._buildSelections(this._campaigns);
    if (this.selections.length > 0) {
      this._updateVisualization(this.selections[0]);
    }
  }

  onSelectionsChange(items: MatListOption[]) {
    // The selection list is configured to allow single item selection only.
    let selection: Selection = items[0].value;
    this._updateVisualization(selection);
  }

  private _buildSelections(campaigns: Campaign[]): Selection[] {
    let selections: Selection[] = [];
    if (campaigns.length > 1) {
      selections.push({
        label: 'Synthèse',
        type: 'synthese',
        campaigns: campaigns,
      });
    }
    let previousCampaign = undefined;
    campaigns.forEach((campaign) => {
      if (previousCampaign !== undefined) {
        selections.push({
          label: `Évolution`,
          type: 'evolution',
          campaigns: [previousCampaign, campaign],
        });
      }
      selections.push({
        label: `Campagne ${campaign.startDate}-${campaign.endDate}`,
        type: 'campaign',
        campaigns: [campaign],
      });
      previousCampaign = campaign;
    });
    return selections;
  }

  private _updateVisualization(vizSelection: Selection) {
    this._data
      .getVisualizationBlocks(
        this._indicatorId,
        this._sites,
        vizSelection.campaigns,
        vizSelection.type
      )
      .subscribe((data) => {
        this.vizBlocks = data.vizBlocks;
        this.visualizationError = data.error;
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
