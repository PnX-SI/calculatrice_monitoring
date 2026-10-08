import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import * as moment from 'moment';
import {
  Campaign,
  Indicator,
  parseCampaigns,
  Protocol,
  serializeCampaigns,
  SitesGroup,
} from '../../interfaces';
import { DataService } from '../../services/data.service';

interface SitesGroupChoice extends SitesGroup {
  disabled?: boolean;
}

const noOverlappedCampaignsValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const format = 'YYYY-MM-DD';
  const campaigns: Campaign[] = control.value;
  let overlapSpotted = false;
  campaigns.forEach((camp1) => {
    campaigns.forEach((camp2) => {
      if (camp1 !== camp2) {
        const start1 = moment(camp1.startDate, format);
        const end1 = moment(camp1.endDate, format);
        const start2 = moment(camp2.startDate, format);
        const end2 = moment(camp2.endDate, format);
        if (
          !(
            (start1.isBefore(start2) && end1.isBefore(start2)) ||
            (start2.isBefore(start1) && end2.isBefore(start1))
          )
        ) {
          overlapSpotted = true;
        }
      }
    });
  });
  return overlapSpotted ? { campaignsOverlap: true } : null;
};

const endAfterStartValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const format = 'YYYY-MM-DD';
  const start = moment(control.value.startDate, format);
  const end = moment(control.value.endDate, format);
  return end.isBefore(start) ? { endIsBeforeStart: true } : null;
};

@Component({
  selector: 'pnx-calc-viz-params-form',
  templateUrl: './visualization-params-form.component.html',
  styleUrls: ['./visualization-params-form.component.css'],
})
export class VisualizationParamsFormComponent implements OnInit {
  campaignForm: FormGroup;
  sitesGroupChoices: Array<SitesGroupChoice> = undefined;
  protected protocolId: number | undefined;
  private sitesGroups: Array<SitesGroup> = undefined;
  private protocolCode: string = undefined;

  constructor(
    private _formBuilder: FormBuilder,
    private _data: DataService,
    private _router: Router,
    private _route: ActivatedRoute
  ) {
    this.campaignForm = this._formBuilder.group({
      sitesGroup: [null, Validators.required],
      campaigns: this._formBuilder.array([], { validators: noOverlappedCampaignsValidator }),
    });
  }

  ngOnInit(): void {
    this._route.params.subscribe((params) => {
      const indicatorId = Number(params.indicatorId);
      this._data.getIndicator(indicatorId).subscribe((indicator: Indicator) => {
        this.protocolId = indicator.protocolId;
        this._data.getProtocol(indicator.protocolId).subscribe((protocol: Protocol) => {
          this.protocolCode = protocol.code;
          this._data.getSitesGroups(this.protocolCode).subscribe((data: Array<SitesGroup>) => {
            this.sitesGroups = data;
            this.sitesGroupChoices = this.getSitesGroupChoices(data);
            this._initFormValues(indicatorId);
          });
        });
      });
    });

    this.campaignForm.valueChanges.subscribe((formValues) => {
      if (formValues.sitesGroup || (formValues.campaigns && formValues.campaigns.length > 0)) {
        const campaignsStr = serializeCampaigns(formValues.campaigns);
        this._router.navigate([], {
          relativeTo: this._route,
          queryParams: {
            sitesGroup: formValues.sitesGroup || null,
            campaigns: campaignsStr || null,
          },
          queryParamsHandling: 'merge',
          replaceUrl: true,
        });
      }
    });
  }

  /**
   * Getter pratique pour accéder facilement au FormArray depuis le template.
   */
  get campaigns(): FormArray {
    return this.campaignForm.get('campaigns') as FormArray;
  }

  /**
   * Crée un nouveau FormGroup pour une campagne.
   */
  newCampaign(): FormGroup {
    return this._formBuilder.group(
      {
        startDate: ['', Validators.required],
        endDate: ['', Validators.required],
      },
      { validators: endAfterStartValidator }
    );
  }

  /**
   * Ajoute une nouvelle campagne au FormArray.
   */
  addCampaign() {
    let newCampaign = this.newCampaign();
    this.campaigns.push(newCampaign);
    const nbCampaigns = this.campaigns.value.length;
    if (nbCampaigns > 1) {
      const previousCampaign: Campaign = this.campaigns.value[nbCampaigns - 2];
      const newCampaignStart = this.getNextDay(previousCampaign.endDate);
      newCampaign.patchValue({
        startDate: newCampaignStart,
        endDate: this.getNextYear(newCampaignStart),
      });
    }
  }

  /**
   * Supprime une campagne à un index spécifique.
   */
  removeCampaign(campaignIndex: number) {
    this.campaigns.removeAt(campaignIndex);
  }

  onStartDateChange(campaignForm: FormControl) {
    if (!campaignForm.value.endDate) {
      campaignForm.patchValue({ endDate: this.getNextYear(campaignForm.value.startDate) });
    }
  }

  /**
   * Gère la soumission du formulaire.
   */
  onSubmit() {
    if (this.campaignForm.valid) {
      const sitesGroupId = this.campaignForm.value.sitesGroup;
      const campaigns = this.campaignForm.value.campaigns;
      this._data
        .getSites(
          this.protocolCode,
          this.sitesGroups.find((item) => item.id === sitesGroupId)
        )
        .subscribe((sites) => {
          const indicatorId = this._route.snapshot.params.indicatorId;
          sessionStorage.setItem(
            `calc-viz-params:${indicatorId}`,
            JSON.stringify({ sites, campaigns, sitesGroupId })
          );
          this._router.navigate(['..'], {
            relativeTo: this._route,
            queryParams: {
              sitesGroup: sitesGroupId,
              campaigns: serializeCampaigns(campaigns),
            },
          });
        });
    } else {
      console.error('Le formulaire contient des erreurs.');
    }
  }

  private _initFormValues(indicatorId: number) {
    const queryParams = this._route.snapshot.queryParams;
    let sitesGroupId: number | undefined = queryParams['sitesGroup']
      ? Number(queryParams['sitesGroup'])
      : undefined;
    let campaignsList: Campaign[] = queryParams['campaigns']
      ? parseCampaigns(queryParams['campaigns'])
      : [];

    if (!sitesGroupId || campaignsList.length === 0) {
      const cachedParams = sessionStorage.getItem(`calc-viz-params:${indicatorId}`);
      if (cachedParams) {
        try {
          const parsed = JSON.parse(cachedParams);
          if (!sitesGroupId && parsed.sitesGroupId) {
            sitesGroupId = Number(parsed.sitesGroupId);
          }
          if (campaignsList.length === 0 && Array.isArray(parsed.campaigns)) {
            campaignsList = parsed.campaigns;
          }
        } catch (error) {
          console.error('Failed to parse cached viz params', error);
        }
      }
    }

    if (sitesGroupId) {
      this.campaignForm.patchValue({ sitesGroup: sitesGroupId });
    }

    if (campaignsList.length > 0) {
      while (this.campaigns.length > 0) {
        this.campaigns.removeAt(0);
      }
      campaignsList.forEach((campaign) => {
        const group = this.newCampaign();
        group.patchValue({
          startDate: campaign.startDate,
          endDate: campaign.endDate,
        });
        this.campaigns.push(group);
      });
    } else if (this.campaigns.length === 0) {
      this.addCampaign();
    }
  }

  private getNextDay(date: string) {
    const format = 'YYYY-MM-DD';
    const dateObj = moment(date, format);
    return dateObj.add(1, 'day').format(format);
  }

  private getNextYear(date: string) {
    const format = 'YYYY-MM-DD';
    const dateObj = moment(date, format);
    return dateObj.add(1, 'year').subtract(1, 'day').format(format);
  }

  private getSitesGroupChoices(sitesGroups: SitesGroup[]) {
    return sitesGroups.map<SitesGroupChoice>((group) => {
      let groupChoice: SitesGroupChoice = structuredClone(group);
      groupChoice.disabled = group.nbSites === 0;
      if (groupChoice.disabled) groupChoice.name = `${groupChoice.name} (aucun site)`;
      return groupChoice;
    });
  }
}
