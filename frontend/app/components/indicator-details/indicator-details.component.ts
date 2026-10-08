import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { IndicatorDetails } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { PermissionService } from '../../services/permission.service';

@Component({
  selector: 'pnx-calc-indicator',
  templateUrl: './indicator-details.component.html',
  styleUrls: ['./indicator-details.component.css'],
})
export class IndicatorDetailsComponent implements OnInit {
  protected indicatorDetails: IndicatorDetails | undefined;
  protected campaignVariables: string[] = [];
  protected overviewVariables: string[] = [];
  protected isLoading = true;

  constructor(
    private _data: DataService,
    private _route: ActivatedRoute,
    private _permissionService: PermissionService
  ) {}

  ngOnInit() {
    this._route.params.subscribe((params) => {
      const indicatorId: number = params.indicatorId;
      this.isLoading = true;
      this._data.getIndicatorDetails(indicatorId).subscribe({
        next: (data: IndicatorDetails) => {
          this.indicatorDetails = data;
          this._data.selectedProtocolId = data.protocol.id;
          this.isLoading = false;
        },
        error: () => {
          this.isLoading = false;
        },
      });
      this._data.getIndicatorCodeVariables(indicatorId).subscribe((variables: string[]) => {
        this.campaignVariables = variables;
      });
      this._data.getIndicatorOverviewCodeVariables(indicatorId).subscribe((variables: string[]) => {
        this.overviewVariables = variables;
      });
    });
  }

  canEditIndicator(): boolean {
    return this._permissionService.getAdminPermission('U') > 0;
  }

  canConfigureCampaignBlocks(): boolean {
    if ((this.indicatorDetails?.visualizationBlockConfigs?.length ?? 0) > 0) {
      return true;
    }
    return Boolean(this.indicatorDetails?.code?.trim() && this.campaignVariables?.length > 0);
  }

  getCampaignBlocksTooltip(): string {
    if (this.canConfigureCampaignBlocks()) {
      return '';
    }
    if (!this.indicatorDetails?.code?.trim()) {
      return "Veuillez d'abord renseigner le code pour pouvoir configurer des blocs de visualisation.";
    }
    return 'Le code actuel ne définit aucune variable valide (assignation requise, ex: val = ...).';
  }

  canConfigureOverviewBlocks(): boolean {
    if ((this.indicatorDetails?.overviewVisualizationBlockConfigs?.length ?? 0) > 0) {
      return true;
    }
    return Boolean(
      this.indicatorDetails?.overviewCode?.trim() && this.overviewVariables?.length > 0
    );
  }

  getOverviewBlocksTooltip(): string {
    if (this.canConfigureOverviewBlocks()) {
      return '';
    }
    if (!this.indicatorDetails?.overviewCode?.trim()) {
      return "Veuillez d'abord renseigner le code de synthèse pour pouvoir configurer des blocs de visualisation.";
    }
    return 'Le code de synthèse ne définit aucune variable valide (assignation requise, ex: val = ...).';
  }
}
